"""lowercase user emails"""
from alembic import op
import sqlalchemy as sa


revision = '9f3cbb8a0df2'
down_revision = 'be73c5442ef9'
branch_labels = None
depends_on = None


def upgrade():
    clashes = (
        op.get_bind()
        .execute(
            sa.text(
                'select lower(email) from "user" '
                "group by lower(email) having count(*) > 1"
            )
        )
        .scalars()
        .all()
    )
    if clashes:
        raise RuntimeError(
            f"Cannot lowercase the emails, these addresses differ only by case: {clashes}"
        )
    op.execute('update "user" set email = lower(email)')


def downgrade():
    pass
