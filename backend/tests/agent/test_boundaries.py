import ast
from pathlib import Path

AGENT = Path(__file__).parents[2] / "src" / "agent"


def agent_imports() -> set[str]:
    modules: set[str] = set()
    for path in AGENT.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                modules |= {alias.name for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module)
                modules |= {f"{node.module}.{alias.name}" for alias in node.names}
    return modules


def test_the_agent_does_not_depend_on_the_chat() -> None:
    chat = {m for m in agent_imports() if m == "src.chat" or m.startswith("src.chat.")}

    assert chat == set()


def test_the_agent_does_not_depend_on_any_router() -> None:
    routers = {
        m for m in agent_imports() if m.startswith("src.") and m.endswith(".router")
    }

    assert routers == set()
