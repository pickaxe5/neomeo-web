import uuid
from datetime import datetime

from pydantic import BaseModel


class BriefingItem(BaseModel):
    title: str
    url: str
    reason: str  # 예: "미응답 @멘션", "리뷰 요청", "파일 경로 겹침"


class BriefingOut(BaseModel):
    """B-001~005: 3단 우선순위(내가 답해야 할 것 / 내 작업 영향 변경 / 팀 진행 상황).
    2단계에서 AI 파트가 채울 자리. 현재는 빈 목록을 반환하는 스텁."""

    project_id: uuid.UUID
    user_id: uuid.UUID
    generated_at: datetime
    needs_my_response: list[BriefingItem] = []
    affects_my_work: list[BriefingItem] = []
    team_progress_summary: str | None = None
