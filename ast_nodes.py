from dataclasses import dataclass, field


class Node:
    def accept(self, visitor, *args, **kwargs):
        """Resolves the right accept method for self in visitor."""
        name = f"visit_{type(self).__name__}"
        method = getattr(visitor, name, None)

        if method is None:
            raise NotImplementedError(f"{type(visitor).__name__} has no {name}")

        return method(self, *args, **kwargs)


class NodeVisitor:
    def visit(self, node: Node, *args, **kwargs):
        return node.accept(self, *args, **kwargs)


# Statements


@dataclass
class Program(Node):
    statements: list[Node] = field(default_factory=list)


@dataclass
class Block(Node):
    statements: list[Node] = field(default_factory=list)


@dataclass
class Assign(Node):
    target: Node
    op: str
    value: Node


@dataclass
class Print(Node):
    values: list[Node]


@dataclass
class Break(Node):
    pass


@dataclass
class Continue(Node):
    pass


@dataclass
class Return(Node):
    value: Node | None = None


@dataclass
class If(Node):
    condition: Node
    then_branch: Node
    else_branch: Node | None = None


@dataclass
class While(Node):
    condition: Node
    body: Node


@dataclass
class For(Node):
    variable: "Id"
    range: "Range"
    body: Node


# Expressions


@dataclass
class Id(Node):
    name: str


@dataclass
class Index(Node):
    target: Id
    indices: list[Node]


@dataclass
class Range(Node):
    start: Node
    end: Node


@dataclass
class BinOp(Node):
    op: str
    left: Node
    right: Node


@dataclass
class UnaryOp(Node):
    op: str
    operand: Node


@dataclass
class Transpose(Node):
    operand: Node


@dataclass
class IntNum(Node):
    value: str


@dataclass
class FloatNum(Node):
    value: str


@dataclass
class String(Node):
    value: str


@dataclass
class Array(Node):
    elements: list[Node] = field(default_factory=list)


@dataclass
class Call(Node):
    name: str
    args: list[Node]
