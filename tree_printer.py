import ast_nodes as ast
from ast_nodes import NodeVisitor


class TreePrinter(NodeVisitor):
    """Etap wyświetlania AST — osobna metoda `visit_*` dla każdej klasy węzła."""

    def format(self, node: ast.Node) -> str:
        return "\n".join(self.visit(node, 0))

    @staticmethod
    def _line(indent: int, label: str) -> list[str]:
        return ["  " * indent + label]

    def _children(self, nodes, indent: int) -> list[str]:
        lines = []

        for node in nodes:
            lines.extend(self.visit(node, indent))

        return lines

    # Program i instrukcje

    def visit_Program(self, node: ast.Program, indent: int):
        return self._line(indent, "Program") + self._children(
            node.statements, indent + 1
        )

    def visit_Block(self, node: ast.Block, indent: int):
        return self._line(indent, "Block") + self._children(node.statements, indent + 1)

    def visit_Assign(self, node: ast.Assign, indent: int):
        return self._line(indent, f"Assign: {node.op}") + self._children(
            [node.target, node.value], indent + 1
        )

    def visit_Print(self, node: ast.Print, indent: int):
        return self._line(indent, "Print") + self._children(node.values, indent + 1)

    def visit_Break(self, node: ast.Break, indent: int):
        return self._line(indent, "Break")

    def visit_Continue(self, node: ast.Continue, indent: int):
        return self._line(indent, "Continue")

    def visit_Return(self, node: ast.Return, indent: int):
        children = [] if node.value is None else [node.value]
        return self._line(indent, "Return") + self._children(children, indent + 1)

    def visit_If(self, node: ast.If, indent: int):
        children = [node.condition, node.then_branch]

        if node.else_branch is not None:
            children.append(node.else_branch)

        return self._line(indent, "If") + self._children(children, indent + 1)

    def visit_While(self, node: ast.While, indent: int):
        return self._line(indent, "While") + self._children(
            [node.condition, node.body], indent + 1
        )

    def visit_For(self, node: ast.For, indent: int):
        return self._line(indent, "For") + self._children(
            [node.variable, node.range, node.body], indent + 1
        )

    # Wyrażenia

    def visit_Id(self, node: ast.Id, indent: int):
        return self._line(indent, f"ID: {node.name}")

    def visit_Index(self, node: ast.Index, indent: int):
        return self._line(indent, "Index") + self._children(
            [node.target, *node.indices], indent + 1
        )

    def visit_Range(self, node: ast.Range, indent: int):
        return self._line(indent, "Range") + self._children(
            [node.start, node.end], indent + 1
        )

    def visit_BinOp(self, node: ast.BinOp, indent: int):
        return self._line(indent, f"BinOp: {node.op}") + self._children(
            [node.left, node.right], indent + 1
        )

    def visit_UnaryOp(self, node: ast.UnaryOp, indent: int):
        return self._line(indent, f"UnaryOp: {node.op}") + self._children(
            [node.operand], indent + 1
        )

    def visit_Transpose(self, node: ast.Transpose, indent: int):
        return self._line(indent, "Transpose") + self._children(
            [node.operand], indent + 1
        )

    def visit_IntNum(self, node: ast.IntNum, indent: int):
        return self._line(indent, f"Int: {node.value}")

    def visit_FloatNum(self, node: ast.FloatNum, indent: int):
        return self._line(indent, f"Float: {node.value}")

    def visit_String(self, node: ast.String, indent: int):
        return self._line(indent, f"String: {node.value}")

    def visit_Array(self, node: ast.Array, indent: int):
        return self._line(indent, "Array") + self._children(node.elements, indent + 1)

    def visit_Call(self, node: ast.Call, indent: int):
        return self._line(indent, f"Call: {node.name}") + self._children(
            node.args, indent + 1
        )
