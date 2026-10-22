"""Key chat usage by owner_id, like the other tables"""

from alembic import op

revision = "3a7c1e9d4b20"
down_revision = "671f8739157f"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("chat_usage", "user_id", new_column_name="owner_id")
    op.execute(
        "ALTER TABLE chat_usage RENAME CONSTRAINT chat_usage_user_id_fkey TO chat_usage_owner_id_fkey"
    )


def downgrade():
    op.execute(
        "ALTER TABLE chat_usage RENAME CONSTRAINT chat_usage_owner_id_fkey TO chat_usage_user_id_fkey"
    )
    op.alter_column("chat_usage", "owner_id", new_column_name="user_id")
