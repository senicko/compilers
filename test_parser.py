import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scanner import Scanner
from main import main
from parser import Mparser


EXAMPLES = Path(__file__).parent / "examples" / "lab2"


def parse(text):
    scanner = Scanner()
    return Mparser(scanner).parse(scanner.tokenize(text))


class ParserTests(unittest.TestCase):
    def test_official_examples(self):
        for filename in ("example1.m", "example2.m", "example3.m"):
            path = EXAMPLES / filename
            with self.subTest(file=path.name):
                self.assertTrue(parse(path.read_text(encoding="utf-8")))

    def test_empty_program_and_blocks(self):
        for text in ["", "# komentarz\n", "{}", "{{} x = 1; {print x;}}"]:
            with self.subTest(text=text):
                self.assertTrue(parse(text))

    def test_binary_operators(self):
        for operator in "+ - * / .+ .- .* ./ < > <= >= == !=".split():
            with self.subTest(operator=operator):
                self.assertTrue(parse(f"x = A{operator}B;"))

    def test_assignment_operators(self):
        for operator in "= += -= *= /=".split():
            for target in ["A", "A[i]", "A[i, j]"]:
                with self.subTest(operator=operator, target=target):
                    self.assertTrue(parse(f"{target} {operator} -B';"))

    def test_numbers_strings_and_matrix_operators_without_spaces(self):
        self.assertTrue(parse('x=2.5; y=60.; z=.500; a=1e-3; b=1.e2;'))
        self.assertTrue(parse(r'print "tekst", "say \"hi\"", "# komentarz w napisie";'))
        for operator in [".+", ".-", ".*", "./"]:
            with self.subTest(operator=operator):
                self.assertTrue(parse(f"x=1{operator}2; y=1.5{operator}2.5;"))

    def test_arrays_and_special_functions(self):
        self.assertTrue(parse("v=[]; v=[1,-2,x+3]; A=[[1,2],[3,4]];"))
        for function in ["eye", "zeros", "ones"]:
            with self.subTest(function=function):
                self.assertTrue(parse(f"A={function}(n); B={function}(n+1,m);"))

    def test_index_expressions_and_ranges(self):
        self.assertTrue(parse("x=A[i+1]; A[1:n,2:m+1]+=B[1,2];"))

    def test_nested_control_flow(self):
        self.assertTrue(parse("""
            for i = 1:N
                for j = i:M {
                    while (j > 0) {
                        if (i == j) break;
                        else if (i < j) continue;
                        else return A[i, j];
                    }
                }
            return;
        """))

    def test_else_with_nested_if_and_loop(self):
        self.assertTrue(parse("if (a) if (b) x=1; else x=2;"))
        self.assertTrue(parse("if (a) while (b) if (c) x=1; else x=2; else x=3;"))
        self.assertTrue(parse("if (a) {if (b) x=1;} else x=2;"))
        with self.assertRaises(SyntaxError):
            parse("if (a) if (b) x=1; else x=2; else x=3; else x=4;")

    def test_expression_combinations(self):
        self.assertTrue(parse("x = 1+2*3-4/2; y = -(A.+B)' .* C';"))
        self.assertTrue(parse("x = a-(b-c); y = --A''; z = (a<b)==(c>d);"))

    def test_comparisons_cannot_be_chained(self):
        for text in ["x=a<b<c;", "if (a==b!=c) print a;", "x=a<=b>c;"]:
            with self.subTest(text=text), self.assertRaises(SyntaxError):
                parse(text)

    def test_whitespace_does_not_change_syntax(self):
        for separator in [" ", "\n", "\r\n", "\r", "\t", " # komentarz\n"]:
            text = separator.join(["for", "i", "=", "1", ":", "N", "{",
                                   "print", '"i="', ",", "i", ";", "}"])
            with self.subTest(separator=separator):
                self.assertTrue(parse(text))

    def test_invalid_statements(self):
        cases = [
            "x=1", "x=;", "x=1 y=2;", "1=x;", "(x+y)=1;", "x=y=1;",
            "A[]=1;", "A[1,]=1;", "x=[1,2;", "x=[1 2];", "x=[1,];",
            "x=zeros();", "x=eye(1,2,3);", "x=foo(1);", "x=1+;",
            "print;", "print 1,;", "break", "{x=1;", "x=1;}",
            "if x<1 x=2;", "if (x<1) else x=2;", "else x=1;",
            "while (x<1)", "for i=1 print i;", "for i=1: print i;",
        ]
        for text in cases:
            with self.subTest(text=text), self.assertRaises(SyntaxError):
                parse(text)

    def test_syntax_error_reports_token_and_line(self):
        with self.assertRaisesRegex(SyntaxError, r"\(3\): Błąd składni.*;\(';\'\)"):
            parse("x=1;\n\ny=;\n")

    def test_eof_error_reports_line(self):
        for newline in ["\n", "\r\n", "\r"]:
            with self.subTest(newline=newline), self.assertRaisesRegex(
                SyntaxError, r"\(3\): Błąd składni: nieoczekiwany koniec pliku"
            ):
                parse(newline.join(["x=1;", "if (x) {", "print x;"]))

    def test_lexical_error_reports_line(self):
        for text in ["x=1;\n@", 'x=1;\nprint "niedomknięty;', "x=1;\nx=.;"]:
            with self.subTest(text=text), self.assertRaisesRegex(
                ValueError, r"Line 2, column"
            ):
                parse(text)

    def test_parser_can_be_reused_after_error(self):
        scanner = Scanner()
        parser = Mparser(scanner)
        with self.assertRaises(SyntaxError):
            parser.parse(scanner.tokenize("\n\nx=;"))
        self.assertTrue(parser.parse(scanner.tokenize("x=1;")))
        with self.assertRaisesRegex(SyntaxError, r"\(1\):"):
            parser.parse(scanner.tokenize("x="))

    def test_cli_success(self):
        output = io.StringIO()
        errors = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            result = main([str(EXAMPLES / "example3.m")])
        self.assertEqual(result, 0)
        self.assertEqual(output.getvalue(), "Kod jest poprawny składniowo.\n")
        self.assertEqual(errors.getvalue(), "")

    def test_cli_reports_syntax_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.m"
            path.write_text("x=1;\ny=;", encoding="utf-8")
            output = io.StringIO()
            errors = io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                result = main([str(path)])
        self.assertEqual(result, 1)
        self.assertEqual(output.getvalue(), "")
        self.assertIn("(2): Błąd składni", errors.getvalue())

    def test_cli_process_default_and_official_examples(self):
        script = Path(__file__).resolve().with_name("main.py")
        with tempfile.TemporaryDirectory() as directory:
            for filename in (None, "example1.m", "example2.m", "example3.m"):
                command = [sys.executable, str(script)]
                if filename is not None:
                    command.append(str(EXAMPLES.resolve() / filename))
                with self.subTest(file=filename):
                    result = subprocess.run(
                        command, cwd=directory, capture_output=True, text=True
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout, "Kod jest poprawny składniowo.\n")
                    self.assertEqual(result.stderr, "")

    def test_cli_process_errors(self):
        script = Path(__file__).resolve().with_name("main.py")
        cases = [
            ("x=1;\ny=;", "(2): Błąd składni"),
            ("if (x) {\nprint x;", "(2): Błąd składni: nieoczekiwany koniec pliku"),
            ("x=1;\n@", "Line 2, column 1: illegal character"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.m"
            for source, message in cases:
                path.write_text(source, encoding="utf-8")
                with self.subTest(source=source):
                    result = subprocess.run(
                        [sys.executable, str(script), str(path)],
                        cwd=directory, capture_output=True, text=True,
                    )
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, "")
                    self.assertIn(message, result.stderr)
                    self.assertNotIn("Traceback", result.stderr)

    def test_cli_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            errors = io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                result = main([str(Path(directory) / "missing.m")])
        self.assertEqual(result, 1)
        self.assertEqual(output.getvalue(), "")
        self.assertTrue(errors.getvalue())


if __name__ == "__main__":
    unittest.main()
