import uuid
from datetime import datetime

from pydantic import BaseModel


class SeedResponse(BaseModel):
    project_id: uuid.UUID
    team_ids: list[uuid.UUID]
    raw_event_count: int
    message: str


class SimulateTimeRequest(BaseModel):
    """D-003: 기준 시각을 임의로 이동해 자동 마감·브리핑 발생을 재현.
    simulated_now를 생략(None)하면 시뮬레이션을 해제하고 실제 시각으로 되돌린다."""

    project_id: uuid.UUID
    simulated_now: datetime | None = None


class SimulateTimeResult(BaseModel):
    project_id: uuid.UUID
    simulated_now: datetime | None
    applied: bool
