"""add conversation and chat usage"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


revision = 'ae666eac2868'
down_revision = '979b1f68212c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "conversation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=60), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_conversation_owner_id_updated_at",
        "conversation",
        ["owner_id", "updated_at"],
        unique=False,
    )
    op.create_table(
        "chat_usage",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("runs", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "window_start"),
    )


def downgrade():
    op.drop_table("chat_usage")
    op.drop_index("ix_conversation_owner_id_updated_at", table_name="conversation")
    op.drop_table("conversation")
