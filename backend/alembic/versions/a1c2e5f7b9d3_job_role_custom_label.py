"""job role custom label

Revision ID: a1c2e5f7b9d3
Revises: df5447dca412
Create Date: 2026-08-17 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1c2e5f7b9d3'
down_revision: Union[str, None] = 'df5447dca412'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE jobrole ADD VALUE IF NOT EXISTS 'custom'")
    op.add_column(
        'team_memberships',
        sa.Column('job_role_label', sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    # Postgres는 enum에서 값을 제거하는 DDL을 지원하지 않는다 (타입을 새로 만들어 바꿔치기해야
    # 함) — 이 마이그레이션 범위 밖으로 두고, 컬럼 추가만 되돌린다.
    op.drop_column('team_memberships', 'job_role_label')
