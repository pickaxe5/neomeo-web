"""unanswered item manual resolve

Revision ID: df5447dca412
Revises: 1d3e19e39c64
Create Date: 2026-08-12 21:24:44.929994

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'df5447dca412'
down_revision: Union[str, None] = '1d3e19e39c64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'unanswered_items',
        sa.Column('manually_resolved', sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column('unanswered_items', 'manually_resolved')
