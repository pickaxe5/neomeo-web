import enum
import secrets
import uuid
from datetime import datetime, time

from sqlalchemy import DateTime, Enum, ForeignKey, String, Time, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TeamRole(str, enum.Enum):
    LEADER = "leader"  # 팀장
    MEMBER = "member"  # 팀원


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64))  # IANA TZ, 예: "Asia/Seoul"
    work_start: Mapped[time] = mapped_column(Time, default=time(9, 0))
    work_end: Mapped[time] = mapped_column(Time, default=time(18, 0))
    default_language: Mapped[str] = mapped_column(String(8), default="ko")  # MVP: ko, en

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    memberships: Mapped[list["TeamMembership"]] = relationship(back_populates="team")


class TeamMembership(Base):
    __tablename__ = "team_memberships"
    __table_args__ = (UniqueConstraint("user_id", "team_id", name="uq_team_membership"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"))
    role: Mapped[TeamRole] = mapped_column(Enum(TeamRole), default=TeamRole.MEMBER)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    team: Mapped["Team"] = relationship(back_populates="memberships")


class InviteLink(Base):
    """팀원 초대 링크 (O-005). 링크로 가입하면 수락 절차 없이 즉시 해당 팀에 소속된다."""

    __tablename__ = "invite_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"))
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, default=lambda: secrets.token_urlsafe(24))
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
