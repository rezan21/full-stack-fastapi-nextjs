from typing import Annotated

from fastapi import Depends, Request

from src.agent.runtime import AgentRuntime


async def get_runtime(request: Request) -> AgentRuntime:
    """Return the agent runtime the app opened at startup."""
    runtime: AgentRuntime = request.app.state.agent_runtime
    return runtime


RuntimeDep = Annotated[AgentRuntime, Depends(get_runtime)]
