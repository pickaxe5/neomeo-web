import secrets
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))

    # D-003: 설정되어 있으면 자동 마감 워커가 실제 시각 대신 이 값을 "지금"으로 취급한다.
    simulated_now: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    repos: Mapped[list["ProjectRepo"]] = relationship(back_populates="project")


class ProjectRepo(Base):
    """docs/frontend-to-backend-requests.md #11: 프로젝트당 GitHub 레포 다중 연결 (1:N).
    레포 하나는 프로젝트 하나에만 속한다 — 여러 프로젝트가 레포를 공유하는 N:N 시나리오는
    요청받은 적이 없어 다루지 않는다."""

    __tablename__ = "project_repos"
    __table_args__ = (UniqueConstraint("project_id", "repo_id", name="uq_project_repo"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"))

    repo_full_name: Mapped[str] = mapped_column(String(255))  # "owner/repo"
    repo_id: Mapped[str] = mapped_column(String(64))  # GitHub 상의 레포 ID (검증 시 서버가 채움)

    # 이 레포의 GitHub 수집에 쓸 토큰의 소유자 (레포를 연동한 사용자)
    connected_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    gh_last_collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    gh_last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="repos")


class ProjectTeam(Base):
    """프로젝트 참여 팀 (다대다). 프로젝트 참여자 = 참여 팀의 전체 멤버."""

    __tablename__ = "project_teams"
    __table_args__ = (UniqueConstraint("project_id", "team_id", name="uq_project_team"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"))
    team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProjectAdmin(Base):
    """프로젝트 관리자 권한 (프로젝트 설정, 레포 연동, 참여 팀 추가)."""

    __tablename__ = "project_admins"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_admin"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))


class ProjectInviteLink(Base):
    """다른 팀을 프로젝트에 초대하는 링크 (팀 초대 링크와 동일한 패턴, API·테이블은 분리).
    링크를 받은 팀 리더가 자기 팀을 골라 참여시키면 즉시 반영되고 별도 승인 절차는 없다."""

    __tablename__ = "project_invite_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"))
    token: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, default=lambda: secrets.token_urlsafe(24)
    )
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProjectDocument(Base):
    """기획안·정리 문서를 텍스트로 저장 (O-004). 별도 분석 없이 AI 프롬프트에 주입."""

    __tablename__ = "project_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), unique=True)
    content: Mapped[str] = mapped_column(Text)
    # docs/frontend-to-backend-requests.md #14: 파일 업로드로 채운 경우 원본 파일명을 참고용으로
    # 남긴다. 텍스트 직접 입력이면 계속 null. 원본 파일 자체는 저장하지 않고 추출한 텍스트만 남긴다.
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
