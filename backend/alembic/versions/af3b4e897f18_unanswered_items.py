"""unanswered items

Revision ID: af3b4e897f18
Revises: 11ed27b2727f
Create Date: 2026-08-12 21:08:45.522396

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'af3b4e897f18'
down_revision: Union[str, None] = '11ed27b2727f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SIGNAL_VALUES = ('reviewer_requested', 'mentioned', 'author_reply_needed')


def upgrade() -> None:
    signal_enum = postgresql.ENUM(*SIGNAL_VALUES, name='unansweredsignal')
    signal_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'unanswered_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('raw_event_id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('target_user_id', sa.UUID(), nullable=True),
        sa.Column('target_team_id', sa.UUID(), nullable=True),
        sa.Column(
            'signal_type',
            postgresql.ENUM(*SIGNAL_VALUES, name='unansweredsignal', create_type=False),
            nullable=False,
        ),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['raw_event_id'], ['raw_events.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['target_team_id'], ['teams.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('raw_event_id', 'signal_type', 'target_user_id', name='uq_unanswered_item'),
    )
    op.create_index(op.f('ix_unanswered_items_raw_event_id'), 'unanswered_items', ['raw_event_id'])
    op.create_index(op.f('ix_unanswered_items_project_id'), 'unanswered_items', ['project_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_unanswered_items_project_id'), table_name='unanswered_items')
    op.drop_index(op.f('ix_unanswered_items_raw_event_id'), table_name='unanswered_items')
    op.drop_table('unanswered_items')
    postgresql.ENUM(*SIGNAL_VALUES, name='unansweredsignal').drop(op.get_bind(), checkfirst=True)
