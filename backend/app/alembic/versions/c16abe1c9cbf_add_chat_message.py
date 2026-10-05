"""add chat message"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


revision = 'c16abe1c9cbf'
down_revision = 'ae666eac2868'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "chat_message",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("seq", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column(
            "agent_message_id",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=False,
        ),
        sa.Column("role", sqlmodel.sql.sqltypes.AutoString(length=9), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversation.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("conversation_id", "agent_message_id"),
    )
    op.create_index(
        "ix_chat_message_conversation_id_seq",
        "chat_message",
        ["conversation_id", "seq"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_chat_message_conversation_id_seq", table_name="chat_message")
    op.drop_table("chat_message")
