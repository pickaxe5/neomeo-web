import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EventType(str, enum.Enum):
    PR = "pr"                       # PR 생성·머지
    ISSUE = "issue"                 # 이슈 생성·종료
    REVIEW_COMMENT = "review_comment"  # PR 리뷰 코멘트
    COMMIT = "commit"               # 요약 근거·담당 추론에만 사용 (노이즈 큼)


class RawEvent(Base):
    """0층: 구조화 사실 데이터 (언어 무관). 모든 AI 산출물(1층 팀 요약, 2층 개인 브리핑)의
    단일 원천이다. 번역하지 않고 각 언어로 직접 생성하는 원칙(S-005)을 지키려면, 이 테이블에는
    가공된 문장이 아니라 원본 사실만 저장해야 한다."""

    __tablename__ = "raw_events"
    __table_args__ = (
        Index("ix_raw_events_project_created", "project_id", "gh_created_at"),
        # 폴링마다 "업데이트된" PR·이슈를 다시 조회해도 같은 건은 한 번만 저장한다.
        UniqueConstraint("project_id", "type", "github_id", name="uq_raw_event_project_type_github_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), index=True)

    # 귀속 전에는 team_id가 비어있을 수 있다 (G-004: GitHub 핸들로 팀·멤버에 연결)
    team_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)

    type: Mapped[EventType] = mapped_column(Enum(EventType))
    github_id: Mapped[str] = mapped_column(String(64))  # GitHub 상의 PR/이슈/코멘트/커밋 ID
    actor_handle: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)

    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(500))  # 모든 AI 산출물의 근거 링크 (L-004)
    state: Mapped[str | None] = mapped_column(String(32), nullable=True)  # open/closed/merged 등

    # 커밋 전용: 변경 파일 경로 목록 (G-005, 담당 영역 추론에 사용)
    file_paths: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    gh_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    gh_closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    raw_payload: Mapped[dict] = mapped_column(JSONB)  # GitHub API 원본 응답 보관
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
