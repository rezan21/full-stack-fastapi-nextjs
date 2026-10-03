from sqlmodel import Session

from app.models import Item
from tests.utils.user import create_random_user
from tests.utils.utils import random_lower_string


def create_random_item(db: Session) -> Item:
    user = create_random_user(db)
    item = Item(
        title=random_lower_string(),
        description=random_lower_string(),
        owner_id=user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
