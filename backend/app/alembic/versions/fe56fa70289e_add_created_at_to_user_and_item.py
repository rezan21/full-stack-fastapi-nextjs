"""Add created_at to User and Item"""
from alembic import op
import sqlalchemy as sa


revision = 'fe56fa70289e'
down_revision = '1a31ce608336'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('item', sa.Column('created_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('user', sa.Column('created_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column('user', 'created_at')
    op.drop_column('item', 'created_at')
