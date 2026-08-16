import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UnansweredSignal(str, enum.Enum):
    """기능명세서 3.3: 명시적 신호(리뷰어 지정, 멘션)를 코멘트 질문 여부 추론보다 우선한다."""

    REVIEWER_REQUESTED = "reviewer_requested"  # 리뷰어로 지정됐지만 아직 리뷰를 안 남김
    MENTIONED = "mentioned"                    # @멘션됐지만 이후 응답이 없음
    AUTHOR_REPLY_NEEDED = "author_reply_needed"  # 본인 PR/이슈에 코멘트가 달렸지만 후속 응답이 없음


class UnansweredItem(Base):
    """0층 활동 중 아직 답을 받지 못한 질문·리뷰 요청 (3.3). 개인 브리핑(7층) 1단계의
    입력이 된다. 대상자를 특정할 수 없으면 target_user_id를 비워두고 target_team_id만 채운다
    (그마저도 어려우면 둘 다 비워 미해결 상태로만 표시)."""

    __tablename__ = "unanswered_items"
    __table_args__ = (
        UniqueConstraint(
            "raw_event_id", "signal_type", "target_user_id", name="uq_unanswered_item"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("raw_events.id"), index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), index=True)

    target_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    target_team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True
    )
    signal_type: Mapped[UnansweredSignal] = mapped_column(Enum(UnansweredSignal))

    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved: Mapped[bool] = mapped_column(default=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # 기능명세서 7.2: 오프라인으로 해결해 본인이 직접 완료 처리한 경우 True. 이후
    # detect_unanswered_items()의 자동 재계산이 resolved를 덮어쓰지 않도록 막는 플래그다
    # (자동 추론보다 사용자 입력이 우선한다는 이 코드베이스의 공통 원칙, 4.2와 동일한 패턴).
    manually_resolved: Mapped[bool] = mapped_column(default=False)
