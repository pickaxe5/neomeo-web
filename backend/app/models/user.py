import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # GitHub OAuth로 로그인 시점에 자동 확보 (A-001, 핸들 매핑 단계 대체)
    github_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    github_handle: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)

    # GitHub API 수집(G-001~003)에 재사용. 해커톤 범위상 평문 저장 — README 보안 트레이드오프 참고.
    github_access_token: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # 기능명세서 7.1: 직전 열람 시점부터 현재까지를 "부재 구간"으로 삼는 기준값.
    # 브리핑을 생성할 때마다 지금 시각으로 갱신한다.
    last_briefing_viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
