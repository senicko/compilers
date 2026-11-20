from sly import Parser

import ast_nodes as ast
from scanner import Scanner


class Mparser(Parser):
    tokens = Scanner.tokens
    start = "program"
    debugfile = "parser.out"

    precedence = (
        ("nonassoc", "IFX"),
        ("nonassoc", "ELSE"),
        ("left", "+", "-", "DOTADD", "DOTSUB"),
        ("left", "*", "/", "DOTMUL", "DOTDIV"),
        ("right", "UMINUS"),
        ("left", "'"),
    )

    def __init__(self, scanner: Scanner):
        self.scanner = scanner

    @_("statements")
    def program(self, p):
        return ast.Program(p.statements)

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

    @_('PRINT values ";"')
    def statement(self, p):
        return ast.Print(p.values)

    @_('BREAK ";"')
    def statement(self, p):
        return ast.Break()

    @_('CONTINUE ";"')
    def statement(self, p):
        return ast.Continue()

    @_('RETURN value ";"')
    def statement(self, p):
        return ast.Return(p.value)

    @_('RETURN ";"')
    def statement(self, p):
        return ast.Return()

    @_('"{" statements "}"')
    def statement(self, p):
        return ast.Block(p.statements)

    @_('IF "(" condition ")" statement %prec IFX')
    def statement(self, p):
        return ast.If(p.condition, p.statement)

    @_('IF "(" condition ")" statement ELSE statement')
    def statement(self, p):
        return ast.If(p.condition, p.statement0, p.statement1)

    @_('WHILE "(" condition ")" statement')
    def statement(self, p):
        return ast.While(p.condition, p.statement)

    @_(
        'expression "<" expression',
        'expression ">" expression',
        "expression LE expression",
        "expression GE expression",
        "expression EQ expression",
        "expression NE expression",
    )
    def condition(self, p):
        return ast.BinOp(p[1], p.expression0, p.expression1)

    @_('FOR ID "=" range statement')
    def statement(self, p):
        return ast.For(ast.Id(p.ID), p.range, p.statement)

    @_("reference assign_operator value")
    def assignment(self, p):
        return ast.Assign(p.reference, p.assign_operator, p.value)

    @_('"="', "ADDASSIGN", "SUBASSIGN", "MULASSIGN", "DIVASSIGN")
    def assign_operator(self, p):
        return p[0]

    @_("ID")
    def reference(self, p):
        return ast.Id(p.ID)

    @_('ID "[" indices "]"')
    def reference(self, p):
        return ast.Index(ast.Id(p.ID), p.indices)

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
        return ast.Range(p.expression0, p.expression1)

    @_(
        'expression "+" expression',
        'expression "-" expression',
        'expression "*" expression',
        'expression "/" expression',
        "expression DOTADD expression",
        "expression DOTSUB expression",
        "expression DOTMUL expression",
        "expression DOTDIV expression",
    )
    def expression(self, p):
        return ast.BinOp(p[1], p.expression0, p.expression1)

    @_('"-" expression %prec UMINUS')
    def expression(self, p):
        return ast.UnaryOp("-", p.expression)

    @_('expression "\'"')
    def expression(self, p):
        return ast.Transpose(p.expression)

    @_('"(" expression ")"')
    def expression(self, p):
        return p.expression

    @_("reference")
    def expression(self, p):
        return p.reference

    @_("INTNUM")
    def expression(self, p):
        return ast.IntNum(p.INTNUM)

    @_("FLOATNUM")
    def expression(self, p):
        return ast.FloatNum(p.FLOATNUM)

    @_("STRING")
    def expression(self, p):
        return ast.String(p.STRING)

    @_('special_function "(" expression ")"')
    def expression(self, p):
        return ast.Call(p.special_function, [p.expression])

    @_('special_function "(" expression "," expression ")"')
    def expression(self, p):
        return ast.Call(p.special_function, [p.expression0, p.expression1])

    @_("EYE", "ZEROS", "ONES")
    def special_function(self, p):
        return p[0]

    @_("expression", "matrix")
    def value(self, p):
        return p[0]

    @_("value")
    def values(self, p):
        return [p.value]

    @_('values "," value')
    def values(self, p):
        p.values.append(p.value)
        return p.values

    @_('"[" expressions "]"')
    def matrix(self, p):
        return ast.Array(p.expressions)

    @_('"[" rows "]"')
    def matrix(self, p):
        return ast.Array(p.rows)

    @_("vector")
    def rows(self, p):
        return [p.vector]

    @_('rows "," vector')
    def rows(self, p):
        p.rows.append(p.vector)
        return p.rows

    @_('"[" expressions "]"')
    def vector(self, p):
        return ast.Array(p.expressions)

    @_("expression")
    def expressions(self, p):
        return [p.expression]

    @_('expressions "," expression')
    def expressions(self, p):
        p.expressions.append(p.expression)
        return p.expressions

    def error(self, token):
        if token is None:
            raise SyntaxError(
                f"({self.scanner.lineno}): Błąd składni: nieoczekiwany koniec pliku"
            )

        raise SyntaxError(
            f"({token.lineno}): Błąd składni przy tokenie {token.type}({token.value!r})"
        )
