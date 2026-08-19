import uuid
from datetime import datetime

from pydantic import BaseModel


class BriefingItem(BaseModel):
    # needs_my_response 항목만 id를 갖는다 (UnansweredItem 기반이라 7.2 완료 체크 대상이 됨).
    # affects_my_work 항목은 완료 개념이 없는 정보성 항목이라 id가 없다.
    id: uuid.UUID | None = None
    title: str
    url: str
    reason: str  # 예: "미응답 @멘션", "리뷰 요청", "파일 경로 겹침"
    # AI가 채우는 한 줄 설명 (unanswered_items.why_it_matters). needs_my_response 항목만
    # 해당되며, AI 파트 연동 전까지는 null.
    why_it_matters: str | None = None


class BriefingOut(BaseModel):
    """기능명세서 7.1: 3단 우선순위(내가 답해야 할 것 / 내 작업 영향 변경 / 팀 진행 상황).
    1·2단계는 0층 데이터에서 직접 조립되고, 3단계는 AI가 채우는 summary_cards.content를
    참조한다 — AI 파트 연동 전까지는 null."""

    project_id: uuid.UUID
    user_id: uuid.UUID
    generated_at: datetime
    needs_my_response: list[BriefingItem] = []
    affects_my_work: list[BriefingItem] = []
    team_progress_summary: str | None = None


class ResolveUnansweredItemRequest(BaseModel):
    """기능명세서 7.2: 완료 체크(및 취소) 요청. resolved=False로 다시 보내면 처리를 취소한다."""

    resolved: bool = True
