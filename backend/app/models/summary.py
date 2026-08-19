import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CardStatus(str, enum.Enum):
    NORMAL = "normal"        # 이벤트가 있어 정상 생성된 카드
    NO_CHANGE = "no_change"  # 이벤트 없는 구간, "변동 없음" 카드 (S-006)


class SummaryCard(Base):
    """1층: 팀 요약 카드. 내용(content)은 AI 파트가 0층 데이터로부터 언어별로 직접 생성해 채운다
    (S-004·S-005, 번역 금지). 백엔드는 스키마·저장·조회 API만 제공한다."""

    __tablename__ = "summary_cards"
    __table_args__ = (UniqueConstraint("closure_run_id", "language", name="uq_summary_card_language"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    closure_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("closure_runs.id"), index=True)

    language: Mapped[str] = mapped_column(String(8))  # "ko" | "en" (MVP)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # AI 생성 전에는 NULL
    status: Mapped[CardStatus] = mapped_column(Enum(CardStatus), default=CardStatus.NORMAL)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PersonalProgressSummary(Base):
    """1층 개인화: SummaryCard(팀 공통 카드)와 별개로, 사용자별 관점의 마감 요약.
    AI가 아직 채우지 않았으면(NULL) 브리핑은 팀 공통 카드로 폴백한다 (무손실)."""

    __tablename__ = "personal_progress_summaries"
    __table_args__ = (UniqueConstraint("closure_run_id", "user_id", name="uq_personal_progress_summary"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    closure_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("closure_runs.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)

    language: Mapped[str] = mapped_column(String(8))
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # AI 생성 전에는 NULL

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
