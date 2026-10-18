import argparse
import sys
from pathlib import Path

from sly import Lexer


class Scanner(Lexer):
    tokens = {
        DOTADD,
        DOTSUB,
        DOTMUL,
        DOTDIV,
        ADDASSIGN,
        SUBASSIGN,
        MULASSIGN,
        DIVASSIGN,
        LE,
        GE,
        NE,
        EQ,
        IF,
        ELSE,
        FOR,
        WHILE,
        BREAK,
        CONTINUE,
        RETURN,
        EYE,
        ZEROS,
        ONES,
        PRINT,
        ID,
        FLOATNUM,
        INTNUM,
        STRING,
    }

    literals = set("+-*/=<>()[]{}:',;")
    ignore = " \t"
    ignore_comment = r"\#[^\r\n]*"

    # Compound operators precede lierals because SLY tries
    # rules in their declaration order

    DOTADD = r"\.\+"
    DOTSUB = r"\.-"
    DOTMUL = r"\.\*"
    DOTDIV = r"\./"

    ADDASSIGN = r"\+="
    SUBASSIGN = r"-="
    MULASSIGN = r"\*="
    DIVASSIGN = r"/="

    LE = r"<="
    GE = r">="
    NE = r"!="
    EQ = r"=="

    ID = r"[a-zA-Z_][a-zA-Z0-9_]*"
    ID["if"] = IF
    ID["else"] = ELSE
    ID["for"] = FOR
    ID["while"] = WHILE
    ID["break"] = BREAK
    ID["continue"] = CONTINUE
    ID["return"] = RETURN
    ID["eye"] = EYE
    ID["zeros"] = ZEROS
    ID["ones"] = ONES
    ID["print"] = PRINT

    # To make the rules easier to read they are split into parts.
    # SLY doesn't treat attributes prefixed with _ as parsing rules.

    _DIGITS = r"[0-9]+"
    _EXPONENT = rf"[eE][+-]?{_DIGITS}"
    _POINT_FLOAT = rf"{_DIGITS}\.(?![+*/-])[0-9]*|\.{_DIGITS}"

    FLOATNUM = rf"(?:{_POINT_FLOAT})(?:{_EXPONENT})?|{_DIGITS}{_EXPONENT}"
    INTNUM = _DIGITS

    _STRING_CHAR = r'[^"\\\r\n]'
    _ESCAPE = r"\\[^\r\n]"
    STRING = rf'"(?:{_STRING_CHAR}|{_ESCAPE})*"'

    @_(r"\n+")
    def ignore_newline(self, t):
        # This is enough as reding in files in python changes all \r\n to \n
        self.lineno += t.value.count("\n")

    def error(self, token):
        line_start = self.text.rfind("\n", 0, token.index)
        column = token.index - line_start

        if token.value[0] == '"':
            detail = "unterminated string"
        else:
            detail = f"illegal character {token.value[0]!r}"

        # Raising an error here ends the scanning after the first error.
        raise ValueError(f"Line {token.lineno}, column {column}: {detail}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "filename",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parent / "examples" / "example.txt",
        help="source file (default: examples/example.txt beside scanner.py)",
    )

    args = parser.parse_args(argv)

    try:
        text = args.filename.read_text(encoding="utf-8")
        for token in Scanner().tokenize(text):
            print(f"({token.lineno}): {token.type}({token.value})")
    except (OSError, UnicodeError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
