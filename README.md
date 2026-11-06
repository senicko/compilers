# Parser SLY — laboratorium 2 i AST

Wymagania: [strona laboratorium](https://home.agh.edu.pl/~mkuta/tklab/lab2/lab2.html).

## Uruchomienie

Polecenia wykonuj z katalogu `~/Uni/semester5/compilers`.

Sprawdzenie składni:

```sh
.venv/bin/python main.py examples/lab2/example1.m
```

Wynik: `Kod jest poprawny składniowo.`

Wypisanie AST:

```sh
.venv/bin/python main.py examples/lab2/example1.m --ast
```

Bez ścieżki zostanie użyty `examples/lab2/example1.m`, więc działa też:

```sh
.venv/bin/python main.py --ast
```

Zapis drzewa do pliku:

```sh
.venv/bin/python main.py examples/lab2/example1.m --ast > ast.txt
```

Program zwraca kod `0` dla poprawnego wejścia. Błąd trafia na stderr
z numerem linii, a kod zakończenia wynosi `1`. Nie jest wypisywane częściowe AST.

Projekt używa Pythona 3.12 i SLY 0.5 z `requirements.txt`.
Przygotowanie środowiska, jeśli jeszcze go nie ma:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Przykład drzewa

Dla kodu:

```text
x = 1 + 2 * 3;
```

AST wygląda tak:

```text
Program
  Assign: =
    ID: x
    BinOp: +
      Int: 1
      BinOp: *
        Int: 2
        Int: 3
```

`Assign` ma dwoje dzieci: cel przypisania i wyrażenie po prawej stronie.
Mnożenie jest pod dodawaniem, więc stanowi jego prawy argument: `1 + (2 * 3)`.
Wcięcie o dwie spacje oznacza przejście do dziecka.

AST zachowuje istotną strukturę programu. Nie ma w nim średników, przecinków
ani węzłów dla nawiasów grupujących. Kolejność działań wynika z ułożenia węzłów.

## Pliki

| Plik                                                   | Zawartość                                     |
| ------------------------------------------------------ | --------------------------------------------- |
| `scanner.py`                                           | Skaner z poprzedniego laboratorium.           |
| `parser.py`                                            | Reguły SLY budujące AST i obsługa błędów.     |
| `ast_nodes.py`                                         | Klasa węzła i funkcja wypisująca drzewo.      |
| `main.py`                                              | Odczyt pliku, opcja `--ast` i wynik programu. |
| `test_parser.py`, `test_scanner.py`, `test_ast.py`     | Testy składni, skanera, struktury AST i CLI.  |
| `examples/lab2/example1.m`, `example2.m`, `example3.m` | Oficjalne przykłady.                          |

## Zgodność z wymaganiami laboratorium 2

| Wymaganie                       | Realizacja                                                              |
| ------------------------------- | ----------------------------------------------------------------------- |
| Generator SLY i skaner z lab. 1 | `Mparser(Parser)`, `Scanner(Lexer)` i `tokens = Scanner.tokens`.        |
| Operatory binarne i elementowe  | `+`, `-`, `*`, `/`, `.+`, `.-`, `.*`, `./`.                             |
| Wyrażenia relacyjne             | `<`, `>`, `<=`, `>=`, `==`, `!=`.                                       |
| Minus unarny i transpozycja     | `-A`, `A'`; priorytety w `precedence`.                                  |
| Inicjalizacja tablic i macierzy | `[1,2]`, `[[1,2],[3,4]]`.                                               |
| Funkcje macierzowe              | `eye`, `zeros`, `ones`.                                                 |
| Przypisania                     | `=`, `+=`, `-=`, `*=`, `/=`, również do indeksowanych elementów.        |
| Warunki                         | `if`, `if-else`, `else if`; `else` wiąże się z najbliższym wolnym `if`. |
| Pętle                           | `while (warunek)`, `for i = początek:koniec`.                           |
| Instrukcje sterujące            | `break;`, `continue;`, `return;`, `return wyrażenie;`.                  |
| Wypisywanie                     | `print` z jednym lub wieloma wyrażeniami.                               |
| Instrukcje złożone              | Bloki `{ ... }`, również zagnieżdżone.                                  |
| Indeksy i opcjonalne zakresy    | `A[i]`, `A[i,j]`, `A[1:N,2:M]`.                                         |
| Formatowanie i komentarze       | Pomijane przez skaner; obsługa LF, CRLF i CR.                           |
| Błędne wejście                  | Komunikat z numerem linii; kod zakończenia `1`.                         |
| Oficjalne przykłady             | Wszystkie trzy pliki w `examples/lab2` są akceptowane.                  |

Budowanie i wypisywanie AST jest rozszerzeniem zakresu lab. 2.
Parser nadal rozpoznaje te same konstrukcje i zgłasza błędy składni.

## 1. Węzeł i wypisywanie AST

Cały plik `ast_nodes.py`:

```python
from dataclasses import dataclass, field


@dataclass
class Node:
    kind: str
    children: list["Node"] = field(default_factory=list)
    value: str | None = None


def format_ast(node: Node, indent: int = 0) -> str:
    label = node.kind
    if node.value is not None:
        label += f": {node.value}"

    lines = ["  " * indent + label]
    for child in node.children:
        lines.append(format_ast(child, indent + 1))
    return "\n".join(lines)
```

`kind` to rodzaj węzła, `children` to lista jego dzieci, a `value` zawiera
np. operator lub nazwę zmiennej. Wartości liczb i napisów pozostają leksemami
ze skanera, np. `007`, `1e-3`, `"tekst"`. Nie są obliczane ani odkodowywane.

`@dataclass` tworzy konstruktor i porównywanie węzłów.
`default_factory=list` daje każdemu węzłowi własną listę dzieci.
`format_ast` dopisuje etykietę węzła, a następnie rekurencyjnie jego dzieci.

| Węzeł                    | Wartość i kolejność dzieci                             |
| ------------------------ | ------------------------------------------------------ |
| `Program`, `Block`       | Kolejne instrukcje.                                    |
| `Assign`                 | `value`: operator; dzieci: cel, wyrażenie.             |
| `ID`                     | `value`: nazwa zmiennej.                               |
| `Int`, `Float`, `String` | `value`: oryginalny leksem.                            |
| `BinOp`                  | `value`: operator; dzieci: lewy i prawy argument.      |
| `UnaryOp`                | `value`: `-`; dziecko: argument.                       |
| `Transpose`              | Dziecko: transponowane wyrażenie.                      |
| `Array`                  | Elementy tablicy; macierz zawiera dzieci typu `Array`. |
| `Call`                   | `value`: nazwa funkcji; dzieci: argumenty.             |
| `Index`                  | Zmienna, a potem kolejne indeksy lub zakresy.          |
| `Range`                  | Początek i koniec zakresu.                             |
| `If`                     | Warunek, gałąź `if`, opcjonalnie gałąź `else`.         |
| `While`                  | Warunek i ciało pętli.                                 |
| `For`                    | Zmienna pętli, zakres i ciało.                         |
| `Print`                  | Wypisywane wyrażenia.                                  |
| `Return`                 | Zero dzieci lub jedno zwracane wyrażenie.              |
| `Break`, `Continue`      | Bez dzieci.                                            |

## 2. Konfiguracja parsera i priorytety

Początek `parser.py`:

```python
from sly import Parser

from ast_nodes import Node
from scanner import Scanner


class Mparser(Parser):
    tokens = Scanner.tokens
    start = "program"

    # Od najniższego do najwyższego priorytetu.
    precedence = (
        ("nonassoc", "IFX"),
        ("nonassoc", "ELSE"),
        ("nonassoc", "<", ">", "LE", "GE", "EQ", "NE"),
        ("left", "+", "-", "DOTADD", "DOTSUB"),
        ("left", "*", "/", "DOTMUL", "DOTDIV"),
        ("right", "UMINUS"),
        ("left", "'"),
    )

    def __init__(self, scanner: Scanner):
        self.scanner = scanner
```

`tokens` pochodzi ze skanera. `start` wskazuje regułę opisującą cały program.
Reguły są zapisane w dekoratorach `@_(...)`. Nazwa metody jest lewą stroną
produkcji, a napisy w dekoratorze jej prawymi stronami.

SLY zbiera powtarzające się udekorowane metody, np. `expression`.
`_` jest dostępne wewnątrz klasy dziedziczącej z `Parser`.
Metoda zwraca wartość, z której mogą korzystać kolejne reguły.
Teraz reguły zwracają węzły lub listy węzłów zamiast pozostawiać `pass`.

Priorytety są zapisane od najniższego do najwyższego:

- Porównania mają niższy priorytet od działań arytmetycznych.
- `*`, `/`, `.*`, `./` wiążą silniej niż `+`, `-`, `.+`, `.-`.
- `left` daje np. `(a-b)-c` dla `a-b-c`.
- Minus unarny wiąże silniej niż mnożenie, a transpozycja silniej niż minus.
- `nonassoc` odrzuca porównania łańcuchowe, np. `a<b<c`.
- `IFX` i `UMINUS` to pomocnicze priorytety, nie tokeny ze skanera.

## 3. Program, instrukcje i sterowanie

```python
    @_("statements")
    def program(self, p):
        return Node("Program", p.statements)

    @_("statements statement")
    def statements(self, p):
        p.statements.append(p.statement)
        return p.statements

    @_("")
    def statements(self, p):
        return []

    @_('assignment ";"')
    def statement(self, p):
        return p.assignment

    @_('PRINT expressions ";"')
    def statement(self, p):
        return Node("Print", p.expressions)

    @_('BREAK ";"', 'CONTINUE ";"')
    def statement(self, p):
        return Node(p[0].capitalize())

    @_('RETURN expression ";"')
    def statement(self, p):
        return Node("Return", [p.expression])

    @_('RETURN ";"')
    def statement(self, p):
        return Node("Return")

    @_('"{" statements "}"')
    def statement(self, p):
        return Node("Block", p.statements)

    # ELSE wiąże się z najbliższym IF, który nie ma jeszcze ELSE.
    @_('IF "(" expression ")" statement %prec IFX')
    def statement(self, p):
        return Node("If", [p.expression, p.statement])

    @_('IF "(" expression ")" statement ELSE statement')
    def statement(self, p):
        return Node("If", [p.expression, p.statement0, p.statement1])

    @_('WHILE "(" expression ")" statement')
    def statement(self, p):
        return Node("While", [p.expression, p.statement])

    @_('FOR ID "=" range statement')
    def statement(self, p):
        return Node("For", [Node("ID", value=p.ID), p.range, p.statement])
```

`statements` jest listą instrukcji. Produkcja pusta tworzy nową listę,
a `statements statement` dopisuje kolejny węzeł. `program` opakowuje ją
w korzeń `Program`. Wynikiem `parse(...)` jest ten węzeł, również dla pustego programu.

Proste instrukcje kończą się średnikiem. Reguła `assignment ";"` przekazuje
węzeł przypisania. `print`, `return`, `break` i `continue` tworzą własne węzły.
Blok `{ ... }` jest pojedynczą instrukcją zawierającą listę instrukcji.

Warunki `if` i `while` są w nawiasach. Ich ciałem może być pojedyncza
instrukcja lub blok. `else if` jest instrukcją `if` w gałęzi `else`.
Pętla `for` ma postać `for i = początek:koniec statement`.

`%prec IFX` nadaje krótkiej regule `if` niższy priorytet niż `ELSE`.
Dzięki temu `else` trafia do najbliższego `if`, który nie ma jeszcze tej gałęzi.

W `p` dostępne są wyniki składników reguły. `p.expression` oznacza węzeł
warunku. Gdy symbol występuje dwa razy, SLY dodaje sufiksy `0` i `1`,
np. `p.statement0` i `p.statement1` dla dwóch gałęzi.

## 4. Przypisania, indeksy i zakresy

```python
    @_("reference assign_operator expression")
    def assignment(self, p):
        return Node("Assign", [p.reference, p.expression], value=p.assign_operator)

    @_('"="', "ADDASSIGN", "SUBASSIGN", "MULASSIGN", "DIVASSIGN")
    def assign_operator(self, p):
        return p[0]

    @_("ID")
    def reference(self, p):
        return Node("ID", value=p.ID)

    @_('ID "[" indices "]"')
    def reference(self, p):
        return Node("Index", [Node("ID", value=p.ID), *p.indices])

    @_("index")
    def indices(self, p):
        return [p[0]]

    @_('indices "," index')
    def indices(self, p):
        p.indices.append(p[2])
        return p.indices

    @_("expression", "range")
    def index(self, p):
        return p[0]

    @_('expression ":" expression')
    def range(self, p):
        return Node("Range", [p.expression0, p.expression1])
```

`reference` opisuje zmienną albo odwołanie z indeksami.
Przypisanie tworzy `Assign`, którego wartością jest operator, np. `=` lub `+=`.
Lewa strona musi pasować do `reference`, więc `1=x;` i `(a+b)=x;` są błędne.

`Index` przechowuje zmienną i listę indeksów. Indeks jest wyrażeniem
lub węzłem `Range`. Przykłady: `A[i+1]`, `A[i,j]`, `A[1:N,2:M]`.
Zakres ma postać `początek:koniec`. Nie ma wariantu z krokiem `1:2:10`
ani samego `:` jako indeksu.

W regułach `indices` używamy `p[0]` i `p[2]`: `p.index` jest już
właściwością SLY z pozycją w tekście, więc nie oznacza tu wartości reguły `index`.

## 5. Wyrażenia

```python
    @_(
        'expression "+" expression',
        'expression "-" expression',
        'expression "*" expression',
        'expression "/" expression',
        "expression DOTADD expression",
        "expression DOTSUB expression",
        "expression DOTMUL expression",
        "expression DOTDIV expression",
        'expression "<" expression',
        'expression ">" expression',
        "expression LE expression",
        "expression GE expression",
        "expression EQ expression",
        "expression NE expression",
    )
    def expression(self, p):
        return Node("BinOp", [p.expression0, p.expression1], value=p[1])

    @_('"-" expression %prec UMINUS')
    def expression(self, p):
        return Node("UnaryOp", [p.expression], value="-")

    @_('expression "\'"')
    def expression(self, p):
        return Node("Transpose", [p.expression])

    @_('"(" expression ")"')
    def expression(self, p):
        return p.expression

    @_("reference")
    def expression(self, p):
        return p.reference

    @_("INTNUM")
    def expression(self, p):
        return Node("Int", value=p.INTNUM)

    @_("FLOATNUM")
    def expression(self, p):
        return Node("Float", value=p.FLOATNUM)

    @_("STRING")
    def expression(self, p):
        return Node("String", value=p.STRING)

    @_('"[" expressions "]"')
    def expression(self, p):
        return Node("Array", p.expressions)

    @_('"[" "]"')
    def expression(self, p):
        return Node("Array")

    @_('special_function "(" expression ")"')
    def expression(self, p):
        return Node("Call", [p.expression], value=p.special_function)

    @_('special_function "(" expression "," expression ")"')
    def expression(self, p):
        return Node("Call", [p.expression0, p.expression1], value=p.special_function)

    @_("EYE", "ZEROS", "ONES")
    def special_function(self, p):
        return p[0]

    @_("expression")
    def expressions(self, p):
        return [p.expression]

    @_('expressions "," expression')
    def expressions(self, p):
        p.expressions.append(p.expression)
        return p.expressions
```

W operacji binarnej `p.expression0` i `p.expression1` są gotowymi poddrzewami,
a `p[1]` jest operatorem. Powstaje `BinOp` z dwoma dziećmi.
Ta sama akcja obsługuje działania zwykłe, elementowe i porównania.

`DOTADD`, `DOTSUB`, `DOTMUL`, `DOTDIV` odpowiadają `.+`, `.-`, `.*`, `./`.
`LE`, `GE`, `EQ`, `NE` odpowiadają `<=`, `>=`, `==`, `!=`.

Minus unarny tworzy `UnaryOp`; `%prec UMINUS` odróżnia jego priorytet
od odejmowania. Apostrof tworzy `Transpose`.
Nawiasy przekazują wewnętrzny węzeł, bez dodawania osobnego elementu AST.

`expressions` buduje listę używaną w tablicach i `print`.
`[[1,2],[3,4]]` daje `Array` zawierające dwa kolejne węzły `Array`.
Pusta tablica daje `Array` bez dzieci. Elementy rozdzielamy przecinkami;
warianty `[1 2]` i `[1,2;3,4]` nie należą do tej gramatyki.

`Call` przechowuje nazwę funkcji `eye`, `zeros` lub `ones` oraz jeden
lub dwa argumenty. Inne nazwy wywołań, np. `foo(5)`, są odrzucane.

## 6. Błędy i uruchomienie parsera

Ostatnia metoda `parser.py`:

```python
    def error(self, token):
        if token is None:
            raise SyntaxError(
                f"({self.scanner.lineno}): Błąd składni: nieoczekiwany koniec pliku"
            )
        raise SyntaxError(
            f"({token.lineno}): Błąd składni przy tokenie {token.type}({token.value!r})"
        )
```

SLY wywołuje `error`, gdy nie może dopasować tokenu do gramatyki.
W komunikacie jest linia tokenu, przy którym wykryto problem.
Dla `token is None` wejście się skończyło; numer linii pochodzi wtedy ze skanera.
Przy brakującym średniku błąd może zostać wykryty dopiero w następnej linii.
Analiza kończy się na pierwszym błędzie.

Cały `main.py`:

```python
import argparse
import sys
from pathlib import Path

from ast_nodes import format_ast
from parser import Mparser
from scanner import Scanner


def main(argv=None) -> int:
    arguments = argparse.ArgumentParser(
        description="Parser języka macierzowego — lab. 2"
    )
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
```

`argparse` odczytuje ścieżkę i opcję `--ast`.
`Scanner.tokenize` dostarcza tokeny, a `Mparser.parse` zwraca korzeń AST.
Dopiero po poprawnym sparsowaniu całego pliku `format_ast` zamienia drzewo
na tekst. Bez `--ast` program wypisuje komunikat o poprawnej składni.

Wyjątki dotyczą pliku (`OSError`), kodowania (`UnicodeError`), skanera
(`ValueError`) i parsera (`SyntaxError`). `sys.exit(main())` ustawia kod
zakończenia procesu na `0` albo `1`.

## 7. Skaner

Parser korzysta ze skanera `Scanner` z tego projektu. Nazwy tokenów są takie
same jak w `scanner.py`: `DOTADD`, `DOTSUB`, `DOTMUL`, `DOTDIV` oraz
`ADDASSIGN`, `SUBASSIGN`, `MULASSIGN`, `DIVASSIGN`.

Reguły liczb i napisów są rozbite na pomocnicze wzorce:

```python
    _DIGITS = r"[0-9]+"
    _EXPONENT = rf"[eE][+-]?{_DIGITS}"
    _POINT_FLOAT = rf"{_DIGITS}\.(?![+*/-])[0-9]*|\.{_DIGITS}"
```

```python
    FLOATNUM = rf"(?:{_POINT_FLOAT})(?:{_EXPONENT})?|{_DIGITS}{_EXPONENT}"
    INTNUM = _DIGITS

    _STRING_CHAR = r'[^"\\\r\n]'
    _ESCAPE = r"\\[^\r\n]"
    STRING = rf'"(?:{_STRING_CHAR}|{_ESCAPE})*"'
```

`_DIGITS` oznacza cyfry, `_EXPONENT` wykładnik, np. `e-3`, a `_POINT_FLOAT`
liczbę z kropką. `FLOATNUM` jest przed `INTNUM`, więc `2.5` jest jednym tokenem.
Sprawdzenie `(?![+*/-])` zostawia kropkę operatorowi w zapisie `1.+2`.
`STRING` dopuszcza znaki z poprzedzającym `\` i zabrania nowych linii w napisie.
Wartości tokenów pozostają tekstem; parser sprawdza ich typy.

Liczenie linii i zgłaszanie błędów:

```python
    @_(r"\r\n|[\r\n]")
    def ignore_newline(self, t):
        # Obsługuje też tekst przekazany bezpośrednio do tokenize().
        self.lineno += 1

    def error(self, token):
        line_start = max(
            self.text.rfind("\n", 0, token.index),
            self.text.rfind("\r", 0, token.index),
        )
        column = token.index - line_start

        if token.value[0] == '"':
            detail = "unterminated string"
        else:
            detail = f"illegal character {token.value[0]!r}"

        raise ValueError(f"Line {token.lineno}, column {column}: {detail}")
```

Reguła końców linii obsługuje `\n`, `\r\n` i `\r`, również przy bezpośrednim
wywołaniu `tokenize`. Skaner zgłasza `ValueError` z linią i kolumną.
Komentarze, spacje i tabulatory są pomijane przed przekazaniem tokenów parserowi.

## 8. Zakres działania

Parser sprawdza składnię i buduje AST. Nie wykonuje programu ani instrukcji
`print`. Nie sprawdza deklaracji zmiennych, typów, wymiarów macierzy ani wartości
indeksów. `break;` poza pętlą i macierz z wierszami różnej długości przechodzą
analizę składniową; ich kontrola należy do analizy semantycznej.

## 9. Testy

```sh
.venv/bin/python -m unittest -v
```

Testy obejmują oficjalne przykłady, błędne wejścia, numery linii,
różne białe znaki i uruchamianie CLI jako osobnego procesu.
Testy AST sprawdzają kolejność instrukcji, priorytety, nawiasy, indeksy,
macierze, funkcje, zagnieżdżone `if-else`, pętle i dokładny format wydruku.
Sprawdzają też, że `--ast` nie wypisuje częściowego drzewa dla błędnego pliku.
