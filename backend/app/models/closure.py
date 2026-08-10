import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ClosureTrigger(str, enum.Enum):
    AUTO = "auto"      # 10분 폴링 워커가 팀 업무 종료 시각을 지나 자동 실행 (S-001)
    MANUAL = "manual"  # 야근·조기 작업 시 팀장이 버튼으로 추가 실행 (S-002)


class ClosureRun(Base):
    """1 마감 실행 = 1 카드. 수집 범위는 직전 마감 시각 이후 ~ 현재로, 겹치지 않는다 (S-003)."""

    __tablename__ = "closure_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), index=True)
    team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"), index=True)

    trigger_type: Mapped[ClosureTrigger] = mapped_column(Enum(ClosureTrigger))
    range_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    range_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
