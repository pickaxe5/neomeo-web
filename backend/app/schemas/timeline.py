import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.closure import ClosureTrigger
from app.models.summary import CardStatus


class TimelineSourceEvent(BaseModel):
    """docs/frontend-to-backend-requests.md #13: 근거를 URL 나열이 아니라 체인지로그
    형태로 보여주기 위한 구조화된 항목 하나. raw_events 한 행 = 로그 한 줄이다 — 같은
    PR이라도 "생성"과 "머지"는 시각이 다른 별개의 사실이라 각각 한 줄씩 나온다."""

    type: str  # "pull_request" | "issue" | "review_comment" | "commit"
    title: str
    author: str | None
    url: str
    occurred_at: datetime


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
    # 하위 호환용 — URL만 중복 제거해서 나열. 신규 연동은 source_events를 쓰면 된다.
    source_event_urls: list[str]
    source_events: list[TimelineSourceEvent]


class ClosureTriggerRequest(BaseModel):
    """S-002: 팀장이 추가 작업 마감을 수동으로 실행."""

    team_id: uuid.UUID
