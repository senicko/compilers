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
