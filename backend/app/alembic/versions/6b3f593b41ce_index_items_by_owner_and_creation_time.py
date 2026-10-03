"""index items by owner and creation time

Revision ID: 6b3f593b41ce
Revises: a28bd8db53bb
Create Date: 2026-10-04 00:12:01.482308

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '6b3f593b41ce'
down_revision = 'a28bd8db53bb'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_item_owner_id_created_at", "item", ["owner_id", "created_at"]
    )


def downgrade():
    op.drop_index("ix_item_owner_id_created_at", table_name="item")
