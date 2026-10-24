import json
from typing import Any

from ag_ui.core import ToolCallResultEvent
from langchain_core.messages import AIMessage
from sqlmodel.ext.asyncio.session import AsyncSession

from src.agent import streaming as agent_streaming
from src.agent.context import AgentContext
from src.agent.tools.items import MAX_ITEMS
from src.items.models import Item
from src.users.models import User
from tests.utils.agent import ScriptedModel, agent_for, collect, run_input
from tests.utils.user import create_random_user


async def add_items(db: AsyncSession, owner: User, count: int) -> list[Item]:
    items = [
        Item(title=f"{owner.id}-{number}", description=None, owner_id=owner.id)
        for number in range(count)
    ]
    db.add_all(items)
    await db.commit()
    return items


async def list_items_as(owner: User) -> dict[str, Any]:
    call = {"name": "list_items", "args": {}, "id": "call-1"}
    model = ScriptedModel(
        replies=[AIMessage(content="", tool_calls=[call]), AIMessage(content="done")]
    )
    events = await collect(
        agent_streaming.stream_events(
            agent_for(model),
            run_input("what do I have"),
            AgentContext(user_id=owner.id),
        )
    )
    (result,) = (e for e in events if isinstance(e, ToolCallResultEvent))
    return json.loads(str(result.content))


async def test_the_items_tool_lists_only_the_runs_own_items(db: AsyncSession) -> None:
    mine, theirs = await create_random_user(db), await create_random_user(db)
    own = await add_items(db, mine, 2)
    await add_items(db, theirs, 1)

    result = await list_items_as(mine)

    assert result["count"] == 2
    assert {item["title"] for item in result["items"]} == {i.title for i in own}


async def test_the_items_tool_does_not_widen_for_a_superuser(db: AsyncSession) -> None:
    admin, other = await create_random_user(db), await create_random_user(db)
    admin.is_superuser = True
    db.add(admin)
    await db.commit()
    own = await add_items(db, admin, 1)
    await add_items(db, other, 2)

    result = await list_items_as(admin)

    assert result["count"] == 1
    assert [item["title"] for item in result["items"]] == [own[0].title]


async def test_the_items_tool_answers_an_empty_list_for_a_user_with_none(
    db: AsyncSession,
) -> None:
    result = await list_items_as(await create_random_user(db))

    assert result == {"count": 0, "items": []}


async def test_the_items_tool_shows_a_page_and_counts_them_all(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)
    await add_items(db, owner, MAX_ITEMS + 1)

    result = await list_items_as(owner)

    assert result["count"] == MAX_ITEMS + 1
    assert len(result["items"]) == MAX_ITEMS
