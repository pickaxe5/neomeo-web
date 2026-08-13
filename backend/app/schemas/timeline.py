import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.closure import ClosureTrigger
from app.models.summary import CardStatus


class TimelineCardOut(BaseModel):
    """L-001~004: 크로스 타임존 정렬, 시각 병기, 카드 상세·출처는 FE가 표시.
    백엔드는 마감 시각 순 정렬과 근거 이벤트 링크만 제공한다."""

    closure_run_id: uuid.UUID
    team_id: uuid.UUID
    trigger_type: ClosureTrigger
    range_start: datetime
    range_end: datetime
    language: str
    content: str | None
    status: CardStatus
    source_event_urls: list[str]


class ClosureTriggerRequest(BaseModel):
    """S-002: 팀장이 추가 작업 마감을 수동으로 실행."""

    team_id: uuid.UUID
