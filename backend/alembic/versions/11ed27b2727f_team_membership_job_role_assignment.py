"""team membership job role assignment

Revision ID: 11ed27b2727f
Revises: 91ed9546ced8
Create Date: 2026-08-12 21:04:59.233637

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '11ed27b2727f'
down_revision: Union[str, None] = '91ed9546ced8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JOB_ROLE_VALUES = ('frontend', 'backend', 'ai', 'design', 'planning')


def upgrade() -> None:
    job_role_enum = postgresql.ENUM(*JOB_ROLE_VALUES, name='jobrole')
    job_role_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'team_memberships',
        sa.Column('job_role', postgresql.ENUM(*JOB_ROLE_VALUES, name='jobrole', create_type=False), nullable=True),
    )
    op.add_column('team_memberships', sa.Column('assigned_area', sa.String(length=500), nullable=True))
    op.add_column(
        'team_memberships',
        sa.Column('assigned_paths', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        'team_memberships',
        sa.Column('assigned_area_confirmed', sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column('team_memberships', 'assigned_area_confirmed')
    op.drop_column('team_memberships', 'assigned_paths')
    op.drop_column('team_memberships', 'assigned_area')
    op.drop_column('team_memberships', 'job_role')
    postgresql.ENUM(*JOB_ROLE_VALUES, name='jobrole').drop(op.get_bind(), checkfirst=True)
