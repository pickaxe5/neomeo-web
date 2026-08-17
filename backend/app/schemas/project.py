import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.team import TeamOut


class ProjectCreate(BaseModel):
    name: str
    # docs/frontend-to-backend-requests.md #8: 아직 소속 팀이 없는 사용자도 프로젝트를 먼저
    # 만들 수 있도록 선택 입력으로 완화. 없으면 참여 팀 없이 생성되고, 나중에
    # POST /projects/{id}/teams로 팀을 추가한다.
    team_id: uuid.UUID | None = None
    # docs/frontend-to-backend-requests.md #11: 레포 연결은 생성 시점이 아니라 접근 권한
    # 검증이 필요해 POST /projects/{id}/github/connect로만 한다 (여러 개 연결 가능).


class ProjectUpdate(BaseModel):
    name: str


class ProjectOut(BaseModel):
    id: uuid.UUID
    name: str
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
