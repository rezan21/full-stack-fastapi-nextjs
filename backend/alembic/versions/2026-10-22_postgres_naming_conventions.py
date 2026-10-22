"""Name tables, columns and indexes by the Postgres naming conventions"""

from alembic import op

revision = "671f8739157f"
down_revision = "c16abe1c9cbf"
branch_labels = None
depends_on = None

INDEXES = [
    ("ix_user_email", "user_email_idx"),
    ("ix_item_owner_id_created_at", "item_owner_id_created_at_idx"),
    ("ix_auth_throttle_last_failure_at", "auth_throttle_last_failure_at_idx"),
    (
        "ix_conversation_owner_id_updated_at",
        "chat_conversation_owner_id_updated_at_idx",
    ),
    ("ix_chat_message_conversation_id_seq", "chat_message_conversation_id_seq_idx"),
]
CONVERSATION_CONSTRAINTS = [
    ("conversation_pkey", "chat_conversation_pkey"),
    ("conversation_owner_id_fkey", "chat_conversation_owner_id_fkey"),
]


def upgrade():
    op.rename_table("conversation", "chat_conversation")
    for old, new in CONVERSATION_CONSTRAINTS:
        op.execute(f"ALTER TABLE chat_conversation RENAME CONSTRAINT {old} TO {new}")
    for old, new in INDEXES:
        op.execute(f"ALTER INDEX {old} RENAME TO {new}")
    op.alter_column("chat_usage", "window_start", new_column_name="window_started_at")
    op.alter_column("auth_throttle", "locked_until", new_column_name="lock_expires_at")


def downgrade():
    op.alter_column("auth_throttle", "lock_expires_at", new_column_name="locked_until")
    op.alter_column("chat_usage", "window_started_at", new_column_name="window_start")
    for old, new in INDEXES:
        op.execute(f"ALTER INDEX {new} RENAME TO {old}")
    for old, new in CONVERSATION_CONSTRAINTS:
        op.execute(f"ALTER TABLE chat_conversation RENAME CONSTRAINT {new} TO {old}")
    op.rename_table("chat_conversation", "conversation")
