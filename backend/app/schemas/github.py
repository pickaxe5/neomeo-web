import uuid
from datetime import datetime

from pydantic import BaseModel


class GithubConnectRequest(BaseModel):
    repo_full_name: str  # "owner/repo" — repo_id는 GitHub API 응답에서 서버가 채운다.


class GithubConnectResult(BaseModel):
    project_id: uuid.UUID
    connected: bool
    repo_id: str
    repo_full_name: str
    backfill_event_count: int


class GithubRepoStatusOut(BaseModel):
    """G-006: 연결된 레포 1개의 마지막 수집 시각·실패 여부.
    docs/frontend-to-backend-requests.md #11: 프로젝트당 여러 개 연결 가능해 목록으로 내려준다."""

    repo_id: str
    repo_full_name: str
    last_collected_at: datetime | None
    last_error: str | None


class GithubRepoOut(BaseModel):
    """docs/frontend-to-backend-requests.md #1: 내 GitHub 레포 목록."""

    full_name: str
    owner: str
    private: bool
