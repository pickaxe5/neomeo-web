"""personal progress summaries

Revision ID: e1a4c9f2b6d8
Revises: d5f2b8e1a4c7
Create Date: 2026-08-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e1a4c9f2b6d8'
down_revision: Union[str, None] = 'd5f2b8e1a4c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'personal_progress_summaries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('closure_run_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('language', sa.String(length=8), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['closure_run_id'], ['closure_runs.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('closure_run_id', 'user_id', name='uq_personal_progress_summary'),
    )
    op.create_index(
        op.f('ix_personal_progress_summaries_closure_run_id'),
        'personal_progress_summaries',
        ['closure_run_id'],
    )
    op.create_index(
        op.f('ix_personal_progress_summaries_user_id'),
        'personal_progress_summaries',
        ['user_id'],
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_personal_progress_summaries_user_id'), table_name='personal_progress_summaries')
    op.drop_index(op.f('ix_personal_progress_summaries_closure_run_id'), table_name='personal_progress_summaries')
    op.drop_table('personal_progress_summaries')
