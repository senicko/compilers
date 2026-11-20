import ast_nodes as ast
from ast_nodes import NodeVisitor


class TreePrinter(NodeVisitor):
    def _print(self, indent: int, label: str):
        print("|  " * indent + label)

    def _visit_all(self, nodes, indent: int):
        for node in nodes:
            self.visit(node, indent)

    # Statements

    def visit_Program(self, node: ast.Program, indent: int = 0):
        self._visit_all(node.statements, indent)

    def visit_Block(self, node: ast.Block, indent: int = 0):
        self._visit_all(node.statements, indent)

    def visit_Assign(self, node: ast.Assign, indent: int = 0):
        self._print(indent, node.op)
        self._visit_all([node.target, node.value], indent + 1)

    def visit_Print(self, node: ast.Print, indent: int = 0):
        self._print(indent, "PRINT")
        self._visit_all(node.values, indent + 1)

    def visit_Break(self, node: ast.Break, indent: int = 0):
        self._print(indent, "BREAK")

    def visit_Continue(self, node: ast.Continue, indent: int = 0):
        self._print(indent, "CONTINUE")

    def visit_Return(self, node: ast.Return, indent: int = 0):
        self._print(indent, "RETURN")

        if node.value is not None:
            self.visit(node.value, indent + 1)

    def visit_If(self, node: ast.If, indent: int = 0):
        self._print(indent, "IF")
        self.visit(node.condition, indent + 1)
        self._print(indent, "THEN")
        self.visit(node.then_branch, indent + 1)

        if node.else_branch is not None:
            self._print(indent, "ELSE")
            self.visit(node.else_branch, indent + 1)

    def visit_While(self, node: ast.While, indent: int = 0):
        self._print(indent, "WHILE")
        self._visit_all([node.condition, node.body], indent + 1)

    def visit_For(self, node: ast.For, indent: int = 0):
        self._print(indent, "FOR")
        self._visit_all([node.variable, node.range, node.body], indent + 1)

    # Expressions

    def visit_Id(self, node: ast.Id, indent: int = 0):
        self._print(indent, node.name)

    def visit_Index(self, node: ast.Index, indent: int = 0):
        self._print(indent, "REF")
        self._visit_all([node.target, *node.indices], indent + 1)

    def visit_Range(self, node: ast.Range, indent: int = 0):
        self._print(indent, "RANGE")
        self._visit_all([node.start, node.end], indent + 1)

    def visit_BinOp(self, node: ast.BinOp, indent: int = 0):
        self._print(indent, node.op)
        self._visit_all([node.left, node.right], indent + 1)

    def visit_UnaryOp(self, node: ast.UnaryOp, indent: int = 0):
        self._print(indent, node.op)
        self.visit(node.operand, indent + 1)

    def visit_Transpose(self, node: ast.Transpose, indent: int = 0):
        self._print(indent, "TRANSPOSE")
        self.visit(node.operand, indent + 1)

    def visit_IntNum(self, node: ast.IntNum, indent: int = 0):
        self._print(indent, node.value)

    def visit_FloatNum(self, node: ast.FloatNum, indent: int = 0):
        self._print(indent, node.value)

    def visit_String(self, node: ast.String, indent: int = 0):
        self._print(indent, node.value)

    def visit_Array(self, node: ast.Array, indent: int = 0):
        self._print(indent, "VECTOR")
        self._visit_all(node.elements, indent + 1)

    def visit_Call(self, node: ast.Call, indent: int = 0):
        self._print(indent, node.name)
        self._visit_all(node.args, indent + 1)
