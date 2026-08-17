"""project repos multi connect

Revision ID: b7d4f0a3c8e1
Revises: a1c2e5f7b9d3
Create Date: 2026-08-17 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'b7d4f0a3c8e1'
down_revision: Union[str, None] = 'a1c2e5f7b9d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'project_repos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('repo_full_name', sa.String(length=255), nullable=False),
        sa.Column('repo_id', sa.String(length=64), nullable=False),
        sa.Column('connected_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('gh_last_collected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('gh_last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('project_id', 'repo_id', name='uq_project_repo'),
    )

    # 기존에 프로젝트당 1개씩 연결돼 있던 레포를 새 테이블로 옮긴다. gh_last_collected_at을
    # 그대로 이어받아, 마이그레이션 이후 첫 폴링이 전체 재소급이 아니라 이어서 수집되게 한다.
    op.execute(
        """
        INSERT INTO project_repos
            (id, project_id, repo_full_name, repo_id, connected_by_user_id,
             gh_last_collected_at, gh_last_error, created_at)
        SELECT gen_random_uuid(), id, repo_full_name, repo_id, github_connected_by_user_id,
               gh_last_collected_at, gh_last_error, now()
        FROM projects
        WHERE repo_full_name IS NOT NULL AND repo_id IS NOT NULL
          AND github_connected_by_user_id IS NOT NULL
        """
    )

    # raw_events.github_id는 레포 내에서만 유일했다(예: "pr:1:created"). 레포가 여러 개가
    # 되면 서로 다른 레포의 PR #1이 같은 id로 충돌할 수 있어, 이제부터는 repo_id를 접두어로
    # 붙인다 (github_collector.py 참고). 기존에 이미 수집된 행도 같은 형식으로 맞춰
    # 재수집 시 중복 저장되지 않게 한다.
    op.execute(
        """
        UPDATE raw_events
        SET github_id = projects.repo_id || ':' || raw_events.github_id
        FROM projects
        WHERE raw_events.project_id = projects.id AND projects.repo_id IS NOT NULL
        """
    )

    op.drop_column('projects', 'repo_full_name')
    op.drop_column('projects', 'repo_id')
    op.drop_column('projects', 'github_connected_by_user_id')
    op.drop_column('projects', 'gh_last_collected_at')
    op.drop_column('projects', 'gh_last_error')


def downgrade() -> None:
    op.add_column('projects', sa.Column('repo_full_name', sa.String(length=255), nullable=True))
    op.add_column('projects', sa.Column('repo_id', sa.String(length=64), nullable=True))
    op.add_column(
        'projects',
        sa.Column('github_connected_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )
    op.add_column('projects', sa.Column('gh_last_collected_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('projects', sa.Column('gh_last_error', sa.Text(), nullable=True))

    # 프로젝트당 1개만 복원 가능 — 여러 레포가 연결돼 있었다면 가장 먼저 연결된 것만 남는다
    # (되돌리기는 손실이 있을 수 있음을 감수하는 개발 단계용 마이그레이션).
    op.execute(
        """
        UPDATE projects
        SET repo_full_name = pr.repo_full_name,
            repo_id = pr.repo_id,
            github_connected_by_user_id = pr.connected_by_user_id,
            gh_last_collected_at = pr.gh_last_collected_at,
            gh_last_error = pr.gh_last_error
        FROM (
            SELECT DISTINCT ON (project_id) *
            FROM project_repos
            ORDER BY project_id, created_at ASC
        ) pr
        WHERE projects.id = pr.project_id
        """
    )
    op.execute(
        """
        UPDATE raw_events
        SET github_id = substring(github_id FROM position(':' IN github_id) + 1)
        FROM projects
        WHERE raw_events.project_id = projects.id
          AND projects.repo_id IS NOT NULL
          AND raw_events.github_id LIKE projects.repo_id || ':%'
        """
    )

    op.drop_table('project_repos')
