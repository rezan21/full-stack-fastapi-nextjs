"""index items by owner and creation time"""
from alembic import op


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
