"""add auth throttle"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


revision = '979b1f68212c'
down_revision = '165d280e56b9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "auth_throttle",
        sa.Column("key", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column("failures", sa.Integer(), nullable=False),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("key"),
    )
    op.create_index(
        op.f("ix_auth_throttle_last_failure_at"),
        "auth_throttle",
        ["last_failure_at"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_auth_throttle_last_failure_at"), table_name="auth_throttle")
    op.drop_table("auth_throttle")
