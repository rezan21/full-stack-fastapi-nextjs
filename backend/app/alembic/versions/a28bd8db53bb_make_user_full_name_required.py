"""make user full_name required"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


revision = 'a28bd8db53bb'
down_revision = 'fe56fa70289e'
branch_labels = None
depends_on = None


user = sa.table(
    "user",
    sa.column("email", sa.String),
    sa.column("full_name", sa.String),
)


def upgrade():
    op.execute(
        user.update()
        .where(
            sa.or_(
                user.c.full_name.is_(None),
                sa.func.trim(user.c.full_name) == "",
            )
        )
        .values(full_name=user.c.email)
    )
    op.alter_column(
        "user",
        "full_name",
        existing_type=sqlmodel.sql.sqltypes.AutoString(length=255),
        nullable=False,
    )


def downgrade():
    op.alter_column(
        "user",
        "full_name",
        existing_type=sqlmodel.sql.sqltypes.AutoString(length=255),
        nullable=True,
    )
