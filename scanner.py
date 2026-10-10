import sys

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

    literals = {
        "+",
        "-",
        "*",
        "/",
        "=",
        "<",
        ">",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
        ":",
        "'",
        ",",
        ";",
    }

    ignore = " \t"
    ignore_comment = r"\#.*"

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

    FLOATNUM = r"(\d+\.\d*|\.\d+)([eE][+-]?\d+)?|\d+[eE][+-]?\d+"
    INTNUM = r"\d+"
    STRING = r'"([^"\\\n]|\\.)*"'

    @_(r"\n+")
    def ignore_newline(self, t):
        self.lineno += t.value.count("\n")

    def error(self, t):
        print(f"Line {self.lineno}: illegal character '{t.value[0]}'")
        self.index += 1


if __name__ == "__main__":
    try:
        filename = sys.argv[1] if len(sys.argv) > 1 else "example.txt"
        file = open(filename, "r")
    except IOError:
        print("Cannot open {0} file".format(filename))
        sys.exit(0)

    text = file.read()
    lexer = Scanner()

    for tok in lexer.tokenize(text):
        print(f"({tok.lineno}): {tok.type}({tok.value})")
