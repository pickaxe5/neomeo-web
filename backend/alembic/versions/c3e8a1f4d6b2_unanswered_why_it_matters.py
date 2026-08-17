"""unanswered why it matters

Revision ID: c3e8a1f4d6b2
Revises: b7d4f0a3c8e1
Create Date: 2026-08-17 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3e8a1f4d6b2'
down_revision: Union[str, None] = 'b7d4f0a3c8e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'unanswered_items',
        sa.Column('why_it_matters', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('unanswered_items', 'why_it_matters')
