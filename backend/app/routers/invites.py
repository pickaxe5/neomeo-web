from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_team_leader
from app.models.team import InviteLink, Team, TeamMembership, TeamRole
from app.models.user import User
from app.schemas.team import InviteAcceptResponse, InviteLinkOut

router = APIRouter(tags=["invites"])

INVITE_LINK_TTL_DAYS = 30


@router.post("/teams/{team_id}/invite-links", response_model=InviteLinkOut)
def create_invite_link(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InviteLink:
    """O-005: 팀장이 초대 링크를 발급한다."""
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "팀을 찾을 수 없습니다.")
    require_team_leader(db, team_id, current_user)

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
) -> InviteAcceptResponse:
    """O-005: 링크로 가입한 사용자는 자동으로 해당 팀에 소속된다. 별도 수락 절차·설정 없음."""
    invite = db.query(InviteLink).filter(InviteLink.token == token).first()
    if invite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "유효하지 않은 초대 링크입니다.")
    if invite.expires_at and invite.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_410_GONE, "만료된 초대 링크입니다.")

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
