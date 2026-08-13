"""user last briefing viewed at

Revision ID: 1d3e19e39c64
Revises: af3b4e897f18
Create Date: 2026-08-12 21:12:41.786166

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1d3e19e39c64'
down_revision: Union[str, None] = 'af3b4e897f18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('last_briefing_viewed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_briefing_viewed_at')
