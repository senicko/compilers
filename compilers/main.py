import argparse
import sys
from pathlib import Path

from parser import Mparser, format_ast
from scanner import Scanner


def main(argv=None) -> int:
    arguments = argparse.ArgumentParser()

    arguments.add_argument(
        "filename",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parent / "examples" / "lab2" / "example1.m",
        help="plik z kodem źródłowym (domyślnie examples/lab2/example1.m)",
    )

    arguments.add_argument(
        "--ast", action="store_true", help="wypisz abstrakcyjne drzewo składniowe"
    )

    args = arguments.parse_args(argv)

    try:
        text = args.filename.read_text(encoding="utf-8")
        scanner = Scanner()
        parser = Mparser(scanner)
        tree = parser.parse(scanner.tokenize(text))
    except (OSError, UnicodeError, ValueError, SyntaxError) as error:
        print(error, file=sys.stderr)
        return 1

    if args.ast:
        print(format_ast(tree))
    else:
        print("Kod jest poprawny składniowo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
