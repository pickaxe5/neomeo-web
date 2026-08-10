import uuid
from datetime import datetime

from pydantic import BaseModel


class GithubConnectRequest(BaseModel):
    repo_full_name: str  # "owner/repo" — repo_id는 GitHub API 응답에서 서버가 채운다.


class GithubConnectResult(BaseModel):
    project_id: uuid.UUID
    connected: bool
    repo_id: str
    backfill_event_count: int


class GithubStatusOut(BaseModel):
    """G-006: 마지막 수집 시각과 실패 여부 표시."""

    project_id: uuid.UUID
    connected: bool
    last_collected_at: datetime | None
    last_error: str | None
