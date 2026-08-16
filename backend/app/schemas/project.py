import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.team import TeamOut


class ProjectCreate(BaseModel):
    name: str
    repo_full_name: str | None = None  # "owner/repo" — 온보딩에서 레포 목록 중 선택
    repo_id: str | None = None
    team_id: uuid.UUID  # 프로젝트를 만드는 사용자의 소속 팀이 첫 참여 팀이 된다


class ProjectUpdate(BaseModel):
    name: str


class ProjectOut(BaseModel):
    id: uuid.UUID
    name: str
    repo_full_name: str | None
    repo_id: str | None
    created_at: datetime
    # docs/frontend-to-backend-requests.md #4: 요청한 사용자가 project_admins에 속하는지 여부.
    # 비로그인 조회 시 False.
    is_admin: bool = False

    model_config = {"from_attributes": True}


class ProjectDocumentIn(BaseModel):
    content: str


class ProjectDocumentOut(BaseModel):
    project_id: uuid.UUID
    content: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class AddParticipatingTeamRequest(BaseModel):
    team_id: uuid.UUID


class ProjectInviteLinkOut(BaseModel):
    """팀 초대 링크(InviteLinkOut)와 동일한 패턴, 프로젝트 참여용으로 분리."""

    token: str
    project_id: uuid.UUID
    expires_at: datetime | None

    model_config = {"from_attributes": True}


class ProjectInviteAcceptRequest(BaseModel):
    team_id: uuid.UUID  # 링크를 받은 사람이 리더인 팀만 지정 가능 (라우터에서 검증)


class ProjectInviteAcceptResponse(BaseModel):
    project: ProjectOut
    team: TeamOut
    added: bool
