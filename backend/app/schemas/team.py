import uuid
from datetime import datetime, time

from pydantic import BaseModel

from app.models.team import JobRole, TeamRole


class TeamCreate(BaseModel):
    name: str
    country: str | None = None
    timezone: str  # 브라우저에서 자동 감지된 IANA TZ (O-002는 FE 담당, 값은 그대로 저장)
    work_start: time = time(9, 0)
    work_end: time = time(18, 0)
    default_language: str = "ko"


class TeamUpdate(BaseModel):
    name: str | None = None
    country: str | None = None
    timezone: str | None = None
    work_start: time | None = None
    work_end: time | None = None
    default_language: str | None = None


class TeamOut(BaseModel):
    id: uuid.UUID
    name: str
    country: str | None
    timezone: str
    work_start: time
    work_end: time
    default_language: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TeamMemberOut(BaseModel):
    """docs/frontend-to-backend-requests.md #5: 팀원 목록. 이름 대신 GitHub 닉네임으로 표시."""

    user_id: uuid.UUID
    name: str | None
    github_handle: str | None
    role: TeamRole
    # 기능명세서 4.2: 역할·담당 영역. assigned_area_confirmed=False면 assigned_paths는
    # 저장소 활동 기반 추정치이지 확정값이 아니다 (조회 시점마다 최신 활동으로 다시 계산됨).
    job_role: JobRole | None = None
    # docs/frontend-to-backend-requests.md #10: job_role이 CUSTOM일 때만 값이 있다.
    job_role_label: str | None = None
    assigned_area: str | None = None
    assigned_paths: list[str] | None = None
    assigned_area_confirmed: bool = False


class MemberRoleUpdate(BaseModel):
    """docs/frontend-to-backend-requests.md #9A: 리더 위임(leader) 또는 자진 강등(member)."""

    role: TeamRole


class MyAssignmentUpdate(BaseModel):
    """기능명세서 4.2: 본인이 역할·담당 영역을 직접 입력하면, 이후 자동 추론이 덮어쓰지 않는다."""

    job_role: JobRole | None = None
    job_role_label: str | None = None
    assigned_area: str | None = None


class InviteLinkOut(BaseModel):
    token: str
    team_id: uuid.UUID
    expires_at: datetime | None

    model_config = {"from_attributes": True}


class InviteAcceptResponse(BaseModel):
    team: TeamOut
    joined: bool
