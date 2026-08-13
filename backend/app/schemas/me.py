import uuid
from datetime import datetime, time

from pydantic import BaseModel

from app.models.team import TeamRole


class MyTeamOut(BaseModel):
    """C-001 글로벌 내비게이션·프로젝트 전환에 필요한, 로그인한 사용자의 소속 팀 목록."""

    id: uuid.UUID
    name: str
    country: str | None
    timezone: str
    work_start: time
    work_end: time
    default_language: str
    role: TeamRole


class MyProjectOut(BaseModel):
    """C-001: 로그인한 사용자가 속한 팀들이 참여 중인 프로젝트 목록 (프로젝트 전환용)."""

    id: uuid.UUID
    name: str
    repo_full_name: str | None
    repo_id: str | None
    created_at: datetime
    # docs/frontend-to-backend-requests.md #4: 요청한 사용자가 project_admins에 속하는지 여부.
    is_admin: bool = False

    model_config = {"from_attributes": True}
