"""add a token version to user"""
from alembic import op
import sqlalchemy as sa


revision = 'be73c5442ef9'
down_revision = '6b3f593b41ce'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column("token_version", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade():
    op.drop_column("user", "token_version")
