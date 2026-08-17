"""project document source filename

Revision ID: d5f2b8e1a4c7
Revises: c3e8a1f4d6b2
Create Date: 2026-08-17 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd5f2b8e1a4c7'
down_revision: Union[str, None] = 'c3e8a1f4d6b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'project_documents',
        sa.Column('source_filename', sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('project_documents', 'source_filename')
