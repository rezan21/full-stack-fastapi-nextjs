import uuid
from datetime import UTC, datetime

from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import settings
from src.items.models import Item
from tests.utils.item import create_random_item
from tests.utils.user import create_random_user
from tests.utils.utils import random_lower_string


async def test_create_item(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "Foo", "description": "Fighters"}
    response = await client.post(
        f"{settings.API_V1_STR}/items",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert "id" in content
    assert "owner_id" in content


async def test_read_items_rejects_out_of_range_paging(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    for query in ("limit=0", "limit=-1", "limit=101", "skip=-1"):
        response = await client.get(
            f"{settings.API_V1_STR}/items?{query}", headers=superuser_token_headers
        )
        assert response.status_code == 422, query


async def test_read_items_pages_with_skip_and_limit(
    client: AsyncClient, superuser_token_headers: dict[str, str], db: AsyncSession
) -> None:
    for _ in range(3):
        await create_random_item(db)
    url = f"{settings.API_V1_STR}/items"
    count = (await client.get(url, headers=superuser_token_headers)).json()["count"]

    first = (await client.get(f"{url}?limit=2", headers=superuser_token_headers)).json()
    last = await client.get(
        f"{url}?skip={count - 1}&limit=2", headers=superuser_token_headers
    )
    beyond = await client.get(f"{url}?skip={count}", headers=superuser_token_headers)

    assert len(first["data"]) == 2 and first["count"] == count
    assert len(last.json()["data"]) == 1
    assert beyond.json()["data"] == []


async def test_read_item(
    client: AsyncClient, superuser_token_headers: dict[str, str], db: AsyncSession
) -> None:
    item = await create_random_item(db)
    response = await client.get(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == item.title
    assert content["description"] == item.description
    assert content["id"] == str(item.id)
    assert content["owner_id"] == str(item.owner_id)


async def test_read_item_not_found(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    response = await client.get(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


async def test_read_item_not_enough_permissions(
    client: AsyncClient, normal_user_token_headers: dict[str, str], db: AsyncSession
) -> None:
    item = await create_random_item(db)
    response = await client.get(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


async def create_tied_items(
    db: AsyncSession, owner_id: uuid.UUID, count: int
) -> list[str]:
    created_at = datetime.now(UTC)
    items = [
        Item(title=random_lower_string(), owner_id=owner_id, created_at=created_at)
        for _ in range(count)
    ]
    db.add_all(items)
    await db.commit()
    return sorted(str(item.id) for item in items)


async def test_read_items_orders_items_created_at_the_same_moment_by_id(
    client: AsyncClient, normal_user_token_headers: dict[str, str], db: AsyncSession
) -> None:
    me = (
        await client.get(
            f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers
        )
    ).json()
    tied = await create_tied_items(db, uuid.UUID(me["id"]), 5)
    url = f"{settings.API_V1_STR}/items"

    listed: list[str] = []
    while page := (
        await client.get(
            f"{url}?skip={len(listed)}&limit=2", headers=normal_user_token_headers
        )
    ).json()["data"]:
        listed += [item["id"] for item in page]

    assert len(listed) == len(set(listed))
    assert [item_id for item_id in listed if item_id in tied] == tied


async def test_superuser_items_created_at_the_same_moment_are_ordered_by_id(
    client: AsyncClient, superuser_token_headers: dict[str, str], db: AsyncSession
) -> None:
    tied = await create_tied_items(db, (await create_random_user(db)).id, 5)

    listed = (
        await client.get(
            f"{settings.API_V1_STR}/items?limit=100", headers=superuser_token_headers
        )
    ).json()["data"]

    assert [item["id"] for item in listed if item["id"] in tied] == tied


async def test_read_items_only_lists_the_users_own_items(
    client: AsyncClient, normal_user_token_headers: dict[str, str], db: AsyncSession
) -> None:
    me = (
        await client.get(
            f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers
        )
    ).json()
    mine = (
        await client.post(
            f"{settings.API_V1_STR}/items",
            headers=normal_user_token_headers,
            json={"title": "Mine"},
        )
    ).json()
    someone_elses = await create_random_item(db)

    response = await client.get(
        f"{settings.API_V1_STR}/items", headers=normal_user_token_headers
    )

    content = response.json()
    ids = {item["id"] for item in content["data"]}
    assert mine["id"] in ids
    assert str(someone_elses.id) not in ids
    assert {item["owner_id"] for item in content["data"]} == {me["id"]}
    assert content["count"] == len(content["data"])


async def test_read_items(
    client: AsyncClient, superuser_token_headers: dict[str, str], db: AsyncSession
) -> None:
    await create_random_item(db)
    await create_random_item(db)
    response = await client.get(
        f"{settings.API_V1_STR}/items",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 2


async def test_update_item(
    client: AsyncClient, superuser_token_headers: dict[str, str], db: AsyncSession
) -> None:
    item = await create_random_item(db)
    data = {"title": "Updated title", "description": "Updated description"}
    response = await client.patch(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert content["id"] == str(item.id)
    assert content["owner_id"] == str(item.owner_id)


async def test_update_item_not_found(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "Updated title", "description": "Updated description"}
    response = await client.patch(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


async def test_update_item_not_enough_permissions(
    client: AsyncClient, normal_user_token_headers: dict[str, str], db: AsyncSession
) -> None:
    item = await create_random_item(db)
    data = {"title": "Updated title", "description": "Updated description"}
    response = await client.patch(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


async def test_update_item_rejects_a_null_title(
    client: AsyncClient, superuser_token_headers: dict[str, str], db: AsyncSession
) -> None:
    item = await create_random_item(db)
    response = await client.patch(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
        json={"title": None},
    )
    assert response.status_code == 422


async def test_update_item_null_description_clears_it_and_omitted_fields_stay(
    client: AsyncClient, superuser_token_headers: dict[str, str], db: AsyncSession
) -> None:
    item = await create_random_item(db)
    title = item.title
    response = await client.patch(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
        json={"description": None},
    )
    assert response.status_code == 200
    content = response.json()
    assert content["description"] is None
    assert content["title"] == title


async def test_delete_item(
    client: AsyncClient, superuser_token_headers: dict[str, str], db: AsyncSession
) -> None:
    item = await create_random_item(db)
    response = await client.delete(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 204
    assert response.content == b""
    assert (await db.exec(select(Item).where(Item.id == item.id))).first() is None


async def test_delete_item_not_found(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    response = await client.delete(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


async def test_delete_item_not_enough_permissions(
    client: AsyncClient, normal_user_token_headers: dict[str, str], db: AsyncSession
) -> None:
    item = await create_random_item(db)
    response = await client.delete(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"
