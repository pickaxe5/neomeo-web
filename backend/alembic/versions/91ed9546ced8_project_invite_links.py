"""project invite links

Revision ID: 91ed9546ced8
Revises: 787b429d5d42
Create Date: 2026-08-12 18:02:57.497742

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '91ed9546ced8'
down_revision: Union[str, None] = '787b429d5d42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'project_invite_links',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_project_invite_links_token'), 'project_invite_links', ['token'], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_project_invite_links_token'), table_name='project_invite_links')
    op.drop_table('project_invite_links')
