import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import Item
from tests.utils.item import create_random_item
from tests.utils.user import create_random_user
from tests.utils.utils import random_lower_string


def test_create_item(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "Foo", "description": "Fighters"}
    response = client.post(
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


def test_read_items_rejects_out_of_range_paging(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    for query in ("limit=0", "limit=-1", "limit=101", "skip=-1"):
        response = client.get(
            f"{settings.API_V1_STR}/items?{query}", headers=superuser_token_headers
        )
        assert response.status_code == 422, query


def test_read_items_pages_with_skip_and_limit(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    for _ in range(3):
        create_random_item(db)
    url = f"{settings.API_V1_STR}/items"
    count = client.get(url, headers=superuser_token_headers).json()["count"]

    first = client.get(f"{url}?limit=2", headers=superuser_token_headers).json()
    last = client.get(
        f"{url}?skip={count - 1}&limit=2", headers=superuser_token_headers
    )
    beyond = client.get(f"{url}?skip={count}", headers=superuser_token_headers)

    assert len(first["data"]) == 2 and first["count"] == count
    assert len(last.json()["data"]) == 1
    assert beyond.json()["data"] == []


def test_read_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == item.title
    assert content["description"] == item.description
    assert content["id"] == str(item.id)
    assert content["owner_id"] == str(item.owner_id)


def test_read_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_read_item_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def create_tied_items(db: Session, owner_id: uuid.UUID, count: int) -> list[str]:
    created_at = datetime.now(UTC)
    items = [
        Item(title=random_lower_string(), owner_id=owner_id, created_at=created_at)
        for _ in range(count)
    ]
    db.add_all(items)
    db.commit()
    return sorted(str(item.id) for item in items)


def test_read_items_orders_items_created_at_the_same_moment_by_id(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me = client.get(
        f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers
    ).json()
    tied = create_tied_items(db, uuid.UUID(me["id"]), 5)
    url = f"{settings.API_V1_STR}/items"

    listed: list[str] = []
    while page := client.get(
        f"{url}?skip={len(listed)}&limit=2", headers=normal_user_token_headers
    ).json()["data"]:
        listed += [item["id"] for item in page]

    assert len(listed) == len(set(listed))
    assert [item_id for item_id in listed if item_id in tied] == tied


def test_superuser_items_created_at_the_same_moment_are_ordered_by_id(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    tied = create_tied_items(db, create_random_user(db).id, 5)

    listed = client.get(
        f"{settings.API_V1_STR}/items?limit=100", headers=superuser_token_headers
    ).json()["data"]

    assert [item["id"] for item in listed if item["id"] in tied] == tied


def test_read_items_only_lists_the_users_own_items(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me = client.get(
        f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers
    ).json()
    mine = client.post(
        f"{settings.API_V1_STR}/items",
        headers=normal_user_token_headers,
        json={"title": "Mine"},
    ).json()
    someone_elses = create_random_item(db)

    response = client.get(
        f"{settings.API_V1_STR}/items", headers=normal_user_token_headers
    )

    content = response.json()
    ids = {item["id"] for item in content["data"]}
    assert mine["id"] in ids
    assert str(someone_elses.id) not in ids
    assert {item["owner_id"] for item in content["data"]} == {me["id"]}
    assert content["count"] == len(content["data"])


def test_read_items(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_item(db)
    create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 2


def test_update_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.patch(
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


def test_update_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.patch(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_update_item_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.patch(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_update_item_rejects_a_null_title(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.patch(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
        json={"title": None},
    )
    assert response.status_code == 422


def test_update_item_null_description_clears_it_and_omitted_fields_stay(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    title = item.title
    response = client.patch(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
        json={"description": None},
    )
    assert response.status_code == 200
    content = response.json()
    assert content["description"] is None
    assert content["title"] == title


def test_delete_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.delete(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 204
    assert response.content == b""
    assert db.exec(select(Item).where(Item.id == item.id)).first() is None


def test_delete_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_delete_item_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.delete(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"
