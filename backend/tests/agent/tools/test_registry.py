from src.agent.tools.registry import TOOL_NAMES


def test_no_two_tools_share_a_name() -> None:
    assert len(TOOL_NAMES) == len(set(TOOL_NAMES))
