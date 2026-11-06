import unittest

from scanner import Scanner


def scan(text: str) -> list[tuple[str, str, int]]:
    return [(token.type, token.value, token.lineno) for token in Scanner().tokenize(text)]


class ScannerTests(unittest.TestCase):
    def test_operators_and_punctuation(self):
        lexemes = "+ - * / .+ .- .* ./ = += -= *= /= < > <= >= != == ( ) [ ] { } : ' , ;".split()
        types = [
            "+", "-", "*", "/", "DOTADD", "DOTSUB", "DOTMUL", "DOTDIV",
            "=", "ADDASSIGN", "SUBASSIGN", "MULASSIGN", "DIVASSIGN",
            "<", ">", "LE", "GE", "NE", "EQ", "(", ")", "[", "]", "{", "}",
            ":", "'", ",", ";",
        ]
        self.assertEqual(scan(" ".join(lexemes)), [(kind, value, 1) for kind, value in zip(types, lexemes)])

    def test_keywords_and_identifiers(self):
        keywords = "if else for while break continue return eye zeros ones print".split()
        identifiers = ["A", "_", "_A1", "if_result", "iffy", "zeros2", "IF"]
        self.assertEqual(
            scan(" ".join(keywords + identifiers)),
            [(word.upper(), word, 1) for word in keywords]
            + [("ID", word, 1) for word in identifiers],
        )

    def test_numbers_preserve_lexemes(self):
        integers = ["0", "42", "007"]
        floats = ["2.5", "60.500", "60.", ".500", "60.52E2", "1e-3", "1E+2", "1.e2"]
        self.assertEqual(
            scan(" ".join(integers + floats)),
            [("INTNUM", value, 1) for value in integers]
            + [("FLOATNUM", value, 1) for value in floats],
        )
        self.assertEqual(scan("-2"), [("-", "-", 1), ("INTNUM", "2", 1)])

    def test_matrix_operator_after_number(self):
        for operator, kind in [(".+", "DOTADD"), (".-", "DOTSUB"), (".*", "DOTMUL"), ("./", "DOTDIV")]:
            with self.subTest(operator=operator):
                self.assertEqual(scan(f"1{operator}2"), [("INTNUM", "1", 1), (kind, operator, 1), ("INTNUM", "2", 1)])

    def test_strings_and_transpose(self):
        for value in ['""', '"Hello world"', '"# not a comment"', r'"say \"hello\" \\ path"']:
            with self.subTest(value=value):
                self.assertEqual(scan(value), [("STRING", value, 1)])
        self.assertEqual(scan("B'"), [("ID", "B", 1), ("'", "'", 1)])

    def test_comments_whitespace_and_line_numbers(self):
        self.assertEqual(
            scan(" \t# comment\r\nA\n\n# another\rB # at EOF"),
            [("ID", "A", 2), ("ID", "B", 5)],
        )
        self.assertEqual(scan(" \t\n# only a comment"), [])

    def test_assignment_example(self):
        self.assertEqual(scan("A = zeros(5); # comment\nD1 = A.+B';"), [
            ("ID", "A", 1), ("=", "=", 1), ("ZEROS", "zeros", 1),
            ("(", "(", 1), ("INTNUM", "5", 1), (")", ")", 1), (";", ";", 1),
            ("ID", "D1", 2), ("=", "=", 2), ("ID", "A", 2),
            ("DOTADD", ".+", 2), ("ID", "B", 2), ("'", "'", 2), (";", ";", 2),
        ])

    def test_invalid_input_reports_line(self):
        for text in ["\n@", '\n"unterminated', '\n"first\nsecond"']:
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, r"Line 2, column"):
                _ = scan(text)


if __name__ == "__main__":
    _ = unittest.main()
