from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_project_admin, require_team_leader
from app.core.i18n import get_lang, t
from app.models.project import Project, ProjectInviteLink, ProjectTeam
from app.models.team import InviteLink, Team, TeamMembership, TeamRole
from app.models.user import User
from app.schemas.project import (
    ProjectInviteAcceptRequest,
    ProjectInviteAcceptResponse,
    ProjectInviteLinkOut,
    ProjectOut,
)
from app.schemas.team import InviteAcceptResponse, InviteLinkOut

router = APIRouter(tags=["invites"])

INVITE_LINK_TTL_DAYS = 30


@router.post("/teams/{team_id}/invite-links", response_model=InviteLinkOut)
def create_invite_link(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> InviteLink:
    """O-005: 팀장이 초대 링크를 발급한다."""
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("team_not_found", lang))
    require_team_leader(db, team_id, current_user, lang)

    invite = InviteLink(
        team_id=team_id,
        created_by=current_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=INVITE_LINK_TTL_DAYS),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


@router.post("/invite/{token}/accept", response_model=InviteAcceptResponse)
def accept_invite(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> InviteAcceptResponse:
    """O-005: 링크로 가입한 사용자는 자동으로 해당 팀에 소속된다. 별도 수락 절차·설정 없음."""
    invite = db.query(InviteLink).filter(InviteLink.token == token).first()
    if invite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("invite_link_invalid", lang))
    if invite.expires_at and invite.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_410_GONE, t("invite_link_expired", lang))

    team = db.get(Team, invite.team_id)

    existing = (
        db.query(TeamMembership)
        .filter(TeamMembership.team_id == team.id, TeamMembership.user_id == current_user.id)
        .first()
    )
    joined = False
    if existing is None:
        db.add(TeamMembership(user_id=current_user.id, team_id=team.id, role=TeamRole.MEMBER))
        db.commit()
        joined = True

    return InviteAcceptResponse(team=team, joined=joined)


@router.post("/projects/{project_id}/invite-links", response_model=ProjectInviteLinkOut)
def create_project_invite_link(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> ProjectInviteLink:
    """팀 초대 링크(O-005)와 동일한 패턴을 프로젝트 참여 팀 초대에 재사용한다 — 프로젝트
    관리자가 링크를 발급하고, 링크를 받은 팀 리더가 자기 팀을 골라 스스로 참여시킨다.
    관리자가 상대 팀 소속이 아니어도 초대할 수 있고, 상대 팀 동의 없이 끌려들어가지도 않는다."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("project_not_found", lang))
    require_project_admin(db, project_id, current_user, lang)

    invite = ProjectInviteLink(
        project_id=project_id,
        created_by=current_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=INVITE_LINK_TTL_DAYS),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


@router.post("/project-invite/{token}/accept", response_model=ProjectInviteAcceptResponse)
def accept_project_invite(
    token: str,
    payload: ProjectInviteAcceptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> ProjectInviteAcceptResponse:
    """링크를 받은 사람이 본인이 리더인 팀만 골라 프로젝트에 참여시킬 수 있다."""
    invite = db.query(ProjectInviteLink).filter(ProjectInviteLink.token == token).first()
    if invite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("invite_link_invalid", lang))
    if invite.expires_at and invite.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_410_GONE, t("invite_link_expired", lang))

    project = db.get(Project, invite.project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("project_not_found", lang))
    team = db.get(Team, payload.team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("team_not_found", lang))
    require_team_leader(db, payload.team_id, current_user, lang)

    exists = (
        db.query(ProjectTeam)
        .filter(ProjectTeam.project_id == project.id, ProjectTeam.team_id == team.id)
        .first()
    )
    added = False
    if exists is None:
        db.add(ProjectTeam(project_id=project.id, team_id=team.id))
        db.commit()
        added = True

    return ProjectInviteAcceptResponse(
        project=ProjectOut(
            id=project.id,
            name=project.name,
            repo_full_name=project.repo_full_name,
            repo_id=project.repo_id,
            created_at=project.created_at,
            is_admin=False,
        ),
        team=team,
        added=added,
    )
