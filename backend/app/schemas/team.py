import uuid
from datetime import datetime, time

from pydantic import BaseModel


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


class InviteLinkOut(BaseModel):
    token: str
    team_id: uuid.UUID
    expires_at: datetime | None

    model_config = {"from_attributes": True}


class InviteAcceptResponse(BaseModel):
    team: TeamOut
    joined: bool
