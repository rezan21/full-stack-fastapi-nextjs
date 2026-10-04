"""make created_at required"""
from alembic import op
import sqlalchemy as sa


revision = '165d280e56b9'
down_revision = '9f3cbb8a0df2'
branch_labels = None
depends_on = None


TABLES = ("user", "item")


def upgrade():
    for name in TABLES:
        table = sa.table(name, sa.column("created_at", sa.DateTime(timezone=True)))
        op.execute(
            table.update()
            .where(table.c.created_at.is_(None))
            .values(created_at=sa.func.now())
        )
        op.alter_column(
            name,
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
        )


def downgrade():
    for name in TABLES:
        op.alter_column(
            name,
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=True,
        )
