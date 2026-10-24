import uuid
from typing import Any

from ag_ui.core import (
    ResumeEntry,
    RunFinishedEvent,
    RunFinishedInterruptOutcome,
)
from langchain_core.messages import AIMessage
from sqlmodel.ext.asyncio.session import AsyncSession

from src.agent import threads as agent_threads
from src.agent.interrupts import UNANSWERED_RESULT
from src.agent.tools.items import MAX_ITEMS
from src.users.models import User
from tests.utils.agent import (
    THREAD,
    ScriptedModel,
    agent_for,
    answer,
    ask_to_delete,
    calling,
    deleting,
    interrupts_of,
    resume_input,
    run_as,
    run_input,
    tool_call,
    tool_results,
)
from tests.utils.item import add_items, count_items, stored
from tests.utils.user import create_random_superuser, create_random_user

NO_SUCH_ITEM = "You have no item with that id."


async def call_tool(owner: User, name: str, **args: Any) -> dict[str, Any]:
    model = ScriptedModel(
        replies=[
            AIMessage(content="", tool_calls=[tool_call(name, args)]),
            AIMessage(content="done"),
        ]
    )
    (result,) = tool_results(await run_as(owner, agent_for(model), run_input("go")))
    return result


async def create_through_form(
    owner: User, payload: dict[str, Any] | None
) -> list[dict[str, Any]]:
    agent = agent_for(calling([tool_call("create_item", {})], "done"))
    events = await run_as(owner, agent, run_input("add an item"))
    (interrupt,) = interrupts_of(events)
    entry = (
        ResumeEntry(interrupt_id=interrupt.id, status="resolved", payload=payload)
        if payload is not None
        else ResumeEntry(interrupt_id=interrupt.id, status="cancelled")
    )
    return tool_results(await run_as(owner, agent, resume_input([entry])))


def submitted(interrupt_id: str, payload: dict[str, Any]) -> ResumeEntry:
    return ResumeEntry(interrupt_id=interrupt_id, status="resolved", payload=payload)


async def test_the_items_tool_lists_only_the_runs_own_items(db: AsyncSession) -> None:
    mine, theirs = await create_random_user(db), await create_random_user(db)
    own = await add_items(db, mine, 2)
    await add_items(db, theirs, 1)

    result = await call_tool(mine, "list_items")

    assert result["count"] == 2
    assert {item["title"] for item in result["data"]} == {i.title for i in own}


async def test_the_items_tool_does_not_widen_for_a_superuser(db: AsyncSession) -> None:
    admin, other = await create_random_superuser(db), await create_random_user(db)
    own = await add_items(db, admin, 1)
    await add_items(db, other, 2)

    result = await call_tool(admin, "list_items")

    assert result["count"] == 1
    assert [item["title"] for item in result["data"]] == [own[0].title]


async def test_the_items_tool_answers_an_empty_list_for_a_user_with_none(
    db: AsyncSession,
) -> None:
    result = await call_tool(await create_random_user(db), "list_items")

    assert result == {"count": 0, "data": []}


async def test_the_items_tool_shows_a_page_and_counts_them_all(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)
    await add_items(db, owner, MAX_ITEMS + 1)

    result = await call_tool(owner, "list_items")

    assert result["count"] == MAX_ITEMS + 1
    assert len(result["data"]) == MAX_ITEMS


async def test_the_items_tool_skips_the_items_it_is_told_to(db: AsyncSession) -> None:
    owner = await create_random_user(db)
    await add_items(db, owner, MAX_ITEMS + 1)

    result = await call_tool(owner, "list_items", skip=MAX_ITEMS)

    assert result["count"] == MAX_ITEMS + 1
    assert len(result["data"]) == 1


async def test_the_create_tool_adds_the_item_the_user_filled_in(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)

    (result,) = await create_through_form(
        owner, {"title": "Milk", "description": "2 litres"}
    )

    assert result["changed"] is True
    assert result["message"] == "Added “Milk”."
    created = await stored(uuid.UUID(result["item"]["id"]))
    assert created
    assert (created.title, created.description) == ("Milk", "2 litres")
    assert created.owner_id == owner.id


async def test_the_create_tool_adds_an_item_without_a_description(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)

    (result,) = await create_through_form(owner, {"title": "Milk"})

    assert result["item"]["description"] is None


async def test_the_create_tool_refuses_what_the_item_form_refuses(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)
    refused = (
        {"title": ""},
        {"title": "x" * 256},
        {"title": "a", "description": "x" * 256},
    )

    results = [(await create_through_form(owner, payload))[0] for payload in refused]

    assert all(result["changed"] is False for result in results)
    assert await count_items(owner) == 0


async def test_the_form_asks_for_the_items_own_fields_and_limits(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)
    agent = agent_for(calling([tool_call("create_item", {})], "done"))

    (interrupt,) = interrupts_of(await run_as(owner, agent, run_input("add an item")))

    assert interrupt.response_schema is not None
    title = interrupt.response_schema["properties"]["title"]
    description = interrupt.response_schema["properties"]["description"]
    assert (title["minLength"], title["maxLength"]) == (1, 255)
    assert description["anyOf"][0]["maxLength"] == 255


async def test_the_form_starts_with_the_description_the_assistant_was_given(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)
    agent = agent_for(
        calling([tool_call("create_item", {"description": "testing"})], "done")
    )

    events = await run_as(owner, agent, run_input("add an item about testing"))

    (interrupt,) = interrupts_of(events)
    assert interrupt.response_schema is not None
    assert (
        interrupt.response_schema["properties"]["description"]["default"] == "testing"
    )
    assert "default" not in interrupt.response_schema["properties"]["title"]


async def test_an_item_with_a_title_is_added_without_asking(db: AsyncSession) -> None:
    owner = await create_random_user(db)
    agent = agent_for(
        calling(
            [tool_call("create_item", {"title": "Milk", "description": "2 litres"})],
            "done",
        )
    )

    events = await run_as(owner, agent, run_input("add milk, 2 litres"))

    finished = events[-1]
    assert isinstance(finished, RunFinishedEvent)
    assert not isinstance(finished.outcome, RunFinishedInterruptOutcome)
    (result,) = tool_results(events)
    created = await stored(uuid.UUID(result["item"]["id"]))
    assert created
    assert (created.title, created.description) == ("Milk", "2 litres")


async def test_cancelling_the_create_form_creates_nothing(db: AsyncSession) -> None:
    owner = await create_random_user(db)

    (result,) = await create_through_form(owner, None)

    assert result == {
        "changed": False,
        "message": "Cancelled. Nothing was added.",
        "item": None,
    }
    assert await count_items(owner) == 0


async def test_the_update_tool_changes_only_what_it_is_given(db: AsyncSession) -> None:
    owner = await create_random_user(db)
    (item,) = await add_items(db, owner, 1)
    item.description = "kept"
    db.add(item)
    await db.commit()

    result = await call_tool(owner, "update_item", item_id=str(item.id), title="New")

    changed = await stored(item.id)
    assert changed
    assert (changed.title, changed.description) == ("New", "kept")
    assert result["item"]["title"] == "New"
    assert result["message"] == f"Renamed “{item.title}” to “New”."


async def test_the_update_tool_clears_a_description_given_as_empty_text(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)
    (item,) = await add_items(db, owner, 1)
    item.description = "going"
    db.add(item)
    await db.commit()

    result = await call_tool(owner, "update_item", item_id=str(item.id), description="")

    changed = await stored(item.id)
    assert changed
    assert changed.description == ""
    assert changed.title == item.title
    assert result["message"] == f"Updated “{item.title}”."


async def test_the_update_tool_leaves_other_peoples_items_alone(
    db: AsyncSession,
) -> None:
    mine, theirs = await create_random_user(db), await create_random_user(db)
    (item,) = await add_items(db, theirs, 1)

    result = await call_tool(mine, "update_item", item_id=str(item.id), title="Mine")

    assert result["changed"] is False
    assert result["message"] == NO_SUCH_ITEM
    unchanged = await stored(item.id)
    assert unchanged
    assert unchanged.title == item.title


async def test_the_update_tool_does_not_widen_for_a_superuser(
    db: AsyncSession,
) -> None:
    admin, other = await create_random_superuser(db), await create_random_user(db)
    (item,) = await add_items(db, other, 1)

    result = await call_tool(admin, "update_item", item_id=str(item.id), title="Mine")

    assert result["changed"] is False
    unchanged = await stored(item.id)
    assert unchanged
    assert unchanged.title == item.title


async def test_the_update_tool_says_so_when_there_is_no_such_item(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)

    result = await call_tool(
        owner, "update_item", item_id=str(uuid.uuid4()), title="New"
    )

    assert result["message"] == NO_SUCH_ITEM


async def test_the_update_tool_asks_for_the_item_when_nothing_is_given(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)
    (item,) = await add_items(db, owner, 1)
    agent = agent_for(
        calling([tool_call("update_item", {"item_id": str(item.id)})], "done")
    )
    events = await run_as(owner, agent, run_input("edit it"))

    (interrupt,) = interrupts_of(events)
    assert interrupt.response_schema is not None
    assert interrupt.response_schema["properties"]["title"]["default"] == item.title
    resumed = await run_as(
        owner,
        agent,
        resume_input(
            [submitted(interrupt.id, {"title": "Renamed", "description": None})]
        ),
    )

    (result,) = tool_results(resumed)
    changed = await stored(item.id)
    assert changed
    assert (changed.title, changed.description) == ("Renamed", None)
    assert result["message"] == f"Renamed “{item.title}” to “Renamed”."


async def test_cancelling_the_edit_form_changes_nothing(db: AsyncSession) -> None:
    owner = await create_random_user(db)
    (item,) = await add_items(db, owner, 1)
    agent = agent_for(
        calling([tool_call("update_item", {"item_id": str(item.id)})], "done")
    )
    (interrupt,) = interrupts_of(await run_as(owner, agent, run_input("edit it")))
    resumed = await run_as(
        owner,
        agent,
        resume_input([ResumeEntry(interrupt_id=interrupt.id, status="cancelled")]),
    )

    (result,) = tool_results(resumed)
    assert result["changed"] is False
    assert result["message"] == "Cancelled. Nothing was changed."
    unchanged = await stored(item.id)
    assert unchanged
    assert unchanged.title == item.title


async def test_the_update_tool_refuses_what_the_item_form_refuses(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)
    (item,) = await add_items(db, owner, 1)

    results = [
        await call_tool(owner, "update_item", item_id=str(item.id), **args)
        for args in ({"title": ""}, {"description": "x" * 256})
    ]

    assert all(result["changed"] is False for result in results)
    unchanged = await stored(item.id)
    assert unchanged
    assert unchanged.title == item.title


async def test_the_update_tool_says_so_when_the_id_is_not_an_id(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)

    result = await call_tool(owner, "update_item", item_id="1", title="New")

    assert result["message"] == NO_SUCH_ITEM


async def test_an_approved_delete_deletes_the_item(db: AsyncSession) -> None:
    owner = await create_random_user(db)
    (item,) = await add_items(db, owner, 1)
    agent, events = await ask_to_delete(owner, deleting(item))
    (interrupt,) = interrupts_of(events)

    resumed = await run_as(owner, agent, resume_input([answer(interrupt, True)]))

    (result,) = tool_results(resumed)
    assert result == {
        "changed": True,
        "message": f"Deleted “{item.title}”.",
        "item": None,
    }
    assert await stored(item.id) is None
    assert await agent_threads.open_interrupts(agent, THREAD) == []


async def test_a_declined_delete_keeps_the_item_and_says_the_user_declined(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)
    (item,) = await add_items(db, owner, 1)
    agent, events = await ask_to_delete(owner, deleting(item))
    (interrupt,) = interrupts_of(events)

    resumed = await run_as(owner, agent, resume_input([answer(interrupt, False)]))

    (result,) = tool_results(resumed)
    assert result["changed"] is False
    assert "declined" in result["message"]
    assert await stored(item.id)


async def test_an_interrupt_the_user_never_answered_keeps_the_item(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)
    (item,) = await add_items(db, owner, 1)
    agent, events = await ask_to_delete(owner, deleting(item))
    (interrupt,) = interrupts_of(events)

    resumed = await run_as(owner, agent, resume_input([answer(interrupt, None)]))

    (result,) = tool_results(resumed)
    assert result == {"changed": False, "message": UNANSWERED_RESULT, "item": None}
    assert await stored(item.id)


async def test_the_question_is_written_from_the_stored_item_and_not_by_the_model(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)
    (item,) = await add_items(db, owner, 1)
    item.description = "kept for the tax return"
    db.add(item)
    await db.commit()

    _, events = await ask_to_delete(owner, deleting(item))

    (interrupt,) = interrupts_of(events)
    assert interrupt.message == f"Delete “{item.title}”?\nkept for the tax return"


async def test_an_answer_that_is_not_an_approval_never_deletes(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)
    (item,) = await add_items(db, owner, 1)
    agent, events = await ask_to_delete(owner, deleting(item))
    (interrupt,) = interrupts_of(events)
    odd = ResumeEntry(interrupt_id=interrupt.id, status="resolved", payload="yes")

    await run_as(owner, agent, resume_input([odd]))

    assert await stored(item.id)


async def test_an_item_that_is_not_the_users_is_refused_without_asking(
    db: AsyncSession,
) -> None:
    mine, theirs = await create_random_user(db), await create_random_user(db)
    (item,) = await add_items(db, theirs, 1)

    agent, events = await ask_to_delete(mine, deleting(item))

    finished = events[-1]
    assert isinstance(finished, RunFinishedEvent)
    assert not isinstance(finished.outcome, RunFinishedInterruptOutcome)
    assert tool_results(events)[0]["message"] == NO_SUCH_ITEM
    assert await stored(item.id)


async def test_a_superuser_is_asked_about_and_deletes_only_their_own_items(
    db: AsyncSession,
) -> None:
    admin, other = await create_random_superuser(db), await create_random_user(db)
    (item,) = await add_items(db, other, 1)

    _, events = await ask_to_delete(admin, deleting(item))

    assert tool_results(events)[0]["message"] == NO_SUCH_ITEM
    assert await stored(item.id)


async def test_an_id_that_is_not_an_id_is_refused_without_asking(
    db: AsyncSession,
) -> None:
    owner = await create_random_user(db)
    model = calling([tool_call("delete_item", {"item_id": "the first one"})], "done")

    _, events = await ask_to_delete(owner, model)

    assert tool_results(events)[0]["message"] == NO_SUCH_ITEM
