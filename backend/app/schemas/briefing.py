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


class TeamProgressCard(BaseModel):
    """3단계 한 건 = 마감(closure_run) 하나. 카드를 만든 팀과 보는 사람의 팀이 다를 수
    있다(S-005, 다른 팀 카드도 자기 언어로 본다). content는 이 사용자용 개인화 내용이
    있으면 그걸, 없으면 팀 공통 카드로 폴백 — AI가 아직 안 채웠으면 null."""

    team_id: uuid.UUID
    range_start: datetime
    range_end: datetime
    content: str | None = None


class BriefingOut(BaseModel):
    """기능명세서 7.1: 3단 우선순위(내가 답해야 할 것 / 내 작업 영향 변경 / 팀 진행 상황).
    1·2단계는 0층 데이터에서 직접 조립된다. 3단계는 마지막으로 브리핑을 본 이후
    (last_briefing_viewed_at) 마감된 모든 팀의 카드를 시간순으로 담는다 — "자는 동안 다른
    팀이 한 일을 아침에 전부 본다"는 기획 의도상, 가장 최근 것 하나만 보여주면 안 된다."""

    project_id: uuid.UUID
    user_id: uuid.UUID
    generated_at: datetime
    needs_my_response: list[BriefingItem] = []
    affects_my_work: list[BriefingItem] = []
    team_progress_summary: list[TeamProgressCard] = []


class ResolveUnansweredItemRequest(BaseModel):
    """기능명세서 7.2: 완료 체크(및 취소) 요청. resolved=False로 다시 보내면 처리를 취소한다."""

    resolved: bool = True
