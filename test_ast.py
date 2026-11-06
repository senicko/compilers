import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from ast_nodes import Node, format_ast
from main import main
from parser import Mparser
from scanner import Scanner


def parse(source):
    scanner = Scanner()
    return Mparser(scanner).parse(scanner.tokenize(source))


class AstTests(unittest.TestCase):
    def test_empty_program_and_block(self):
        self.assertEqual(parse(""), Node("Program"))
        self.assertEqual(parse("{}"), Node("Program", [Node("Block")]))

    def test_assignment_and_precedence(self):
        expected = Node("Program", [
            Node("Assign", [
                Node("ID", value="x"),
                Node("BinOp", [
                    Node("Int", value="1"),
                    Node("BinOp", [
                        Node("Int", value="2"), Node("Int", value="3"),
                    ], value="*"),
                ], value="+"),
            ], value="="),
        ])
        self.assertEqual(parse("x = 1 + 2 * 3;"), expected)

    def test_left_associativity_and_parentheses(self):
        a = Node("ID", value="a")
        b = Node("ID", value="b")
        c = Node("ID", value="c")
        left = parse("x = a - b - c;").children[0].children[1]
        right = parse("x = a - (b - c);").children[0].children[1]
        self.assertEqual(left, Node("BinOp", [Node("BinOp", [a, b], "-"), c], "-"))
        self.assertEqual(right, Node("BinOp", [a, Node("BinOp", [b, c], "-")], "-"))

    def test_unary_minus_and_transpose(self):
        value = parse("x = -A';").children[0].children[1]
        self.assertEqual(value, Node("UnaryOp", [
            Node("Transpose", [Node("ID", value="A")]),
        ], value="-"))

    def test_literals_preserve_lexemes_and_statement_order(self):
        tree = parse(r'print 007, 1e-3, "say \"hi\""; return;')
        self.assertEqual(tree.children, [
            Node("Print", [
                Node("Int", value="007"),
                Node("Float", value="1e-3"),
                Node("String", value=r'"say \"hi\""'),
            ]),
            Node("Return"),
        ])

    def test_assignment_to_indices_and_ranges(self):
        tree = parse("A[1:N, j+1] += B[2,3];")
        self.assertEqual(tree.children[0], Node("Assign", [
            Node("Index", [
                Node("ID", value="A"),
                Node("Range", [Node("Int", value="1"), Node("ID", value="N")]),
                Node("BinOp", [Node("ID", value="j"), Node("Int", value="1")], "+"),
            ]),
            Node("Index", [
                Node("ID", value="B"), Node("Int", value="2"), Node("Int", value="3"),
            ]),
        ], value="+="))

    def test_arrays_and_function_arguments(self):
        tree = parse("A=[[1,2],[3,4]]; B=[]; C=zeros(2,3); D=eye(4);")
        values = [assignment.children[1] for assignment in tree.children]
        self.assertEqual(values, [
            Node("Array", [
                Node("Array", [Node("Int", value="1"), Node("Int", value="2")]),
                Node("Array", [Node("Int", value="3"), Node("Int", value="4")]),
            ]),
            Node("Array"),
            Node("Call", [Node("Int", value="2"), Node("Int", value="3")], "zeros"),
            Node("Call", [Node("Int", value="4")], "eye"),
        ])

    def test_else_binds_to_nearest_if(self):
        outer = parse("if (a) if (b) print 1; else print 2;").children[0]
        self.assertEqual(outer.kind, "If")
        self.assertEqual(len(outer.children), 2)
        self.assertEqual(outer.children[0], Node("ID", value="a"))
        inner = outer.children[1]
        self.assertEqual(inner, Node("If", [
            Node("ID", value="b"),
            Node("Print", [Node("Int", value="1")]),
            Node("Print", [Node("Int", value="2")]),
        ]))

    def test_loops_blocks_and_control_statements(self):
        tree = parse("for i=1:N {while (i<N) continue; break; return i;}")
        condition = Node("BinOp", [Node("ID", value="i"), Node("ID", value="N")], "<")
        self.assertEqual(tree.children[0], Node("For", [
            Node("ID", value="i"),
            Node("Range", [Node("Int", value="1"), Node("ID", value="N")]),
            Node("Block", [
                Node("While", [condition, Node("Continue")]),
                Node("Break"),
                Node("Return", [Node("ID", value="i")]),
            ]),
        ]))

    def test_tree_format(self):
        self.assertEqual(format_ast(parse("x=1+2*3;")), "\n".join([
            "Program",
            "  Assign: =",
            "    ID: x",
            "    BinOp: +",
            "      Int: 1",
            "      BinOp: *",
            "        Int: 2",
            "        Int: 3",
        ]))

    def test_all_official_asts_can_be_printed(self):
        examples = Path(__file__).parent / "examples" / "lab2"
        for name in ("example1.m", "example2.m", "example3.m"):
            with self.subTest(file=name):
                tree = parse((examples / name).read_text(encoding="utf-8"))
                output = format_ast(tree)
                self.assertTrue(output.startswith("Program\n"))
                self.assertIn("Assign: =", output)

    def test_cli_ast_option(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.m"
            path.write_text("x=1+2*3;", encoding="utf-8")
            output = io.StringIO()
            errors = io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                result = main([str(path), "--ast"])
        self.assertEqual(result, 0)
        self.assertEqual(output.getvalue(), format_ast(parse("x=1+2*3;")) + "\n")
        self.assertEqual(errors.getvalue(), "")

    def test_cli_ast_error_has_no_partial_tree(self):
        script = Path(__file__).resolve().with_name("main.py")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.m"
            path.write_text("x=1;\ny=;", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(script), "--ast", str(path)],
                cwd=directory, capture_output=True, text=True,
            )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("(2): Błąd składni", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
