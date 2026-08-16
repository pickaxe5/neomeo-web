from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_team_leader
from app.core.i18n import get_lang, t
from app.models.closure import ClosureRun
from app.models.github_event import RawEvent
from app.models.project import ProjectTeam
from app.models.summary import SummaryCard
from app.models.team import InviteLink, Team, TeamMembership, TeamRole
from app.models.user import User
from app.schemas.team import MyAssignmentUpdate, TeamCreate, TeamMemberOut, TeamOut, TeamUpdate
from app.services.assignment_service import refresh_unconfirmed_assignments

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Team:
    """O-002 지원 API. 타임존·업무시간 자동 감지·기본값 채우기는 FE 책임이고,
    백엔드는 확인된 값을 그대로 저장한다. 생성자는 자동으로 팀장이 된다."""
    team = Team(**payload.model_dump())
    db.add(team)
    db.flush()

    db.add(TeamMembership(user_id=current_user.id, team_id=team.id, role=TeamRole.LEADER))
    db.commit()
    db.refresh(team)
    return team


@router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: str, db: Session = Depends(get_db), lang: str = Depends(get_lang)) -> Team:
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("team_not_found", lang))
    return team


@router.patch("/{team_id}", response_model=TeamOut)
def update_team(
    team_id: str,
    payload: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> Team:
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("team_not_found", lang))
    require_team_leader(db, team_id, current_user, lang)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(team, field, value)
    db.commit()
    db.refresh(team)
    return team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> None:
    """docs/frontend-to-backend-requests.md #2A: 팀 리더만 가능. team_memberships·invite_links·
    project_teams와, 이 팀 소속 closure_runs/summary_cards까지 함께 정리한다(cascade).
    raw_events는 프로젝트 0층 데이터라 삭제하지 않고 team_id만 비운다(nullable)."""
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("team_not_found", lang))
    require_team_leader(db, team_id, current_user, lang)

    closure_run_ids = [row[0] for row in db.query(ClosureRun.id).filter(ClosureRun.team_id == team_id).all()]
    if closure_run_ids:
        db.query(SummaryCard).filter(SummaryCard.closure_run_id.in_(closure_run_ids)).delete(
            synchronize_session=False
        )
        db.query(ClosureRun).filter(ClosureRun.team_id == team_id).delete(synchronize_session=False)

    db.query(RawEvent).filter(RawEvent.team_id == team_id).update(
        {"team_id": None}, synchronize_session=False
    )
    db.query(InviteLink).filter(InviteLink.team_id == team_id).delete(synchronize_session=False)
    db.query(ProjectTeam).filter(ProjectTeam.team_id == team_id).delete(synchronize_session=False)
    db.query(TeamMembership).filter(TeamMembership.team_id == team_id).delete(synchronize_session=False)

    db.delete(team)
    db.commit()
    return None


@router.post("/{team_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_team(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> None:
    """docs/frontend-to-backend-requests.md #2B: 본인의 team_memberships 행만 제거.
    마지막 남은 리더는 나갈 수 없다 — 팀장 위임 기능이 아직 없어 자동 위임 대신 막고 이유를 응답에 담는다."""
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("team_not_found", lang))

    membership = (
        db.query(TeamMembership)
        .filter(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id)
        .first()
    )
    if membership is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("not_team_member", lang))

    if membership.role == TeamRole.LEADER:
        other_leader_exists = (
            db.query(TeamMembership)
            .filter(
                TeamMembership.team_id == team_id,
                TeamMembership.role == TeamRole.LEADER,
                TeamMembership.user_id != current_user.id,
            )
            .first()
            is not None
        )
        if not other_leader_exists:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, t("last_leader_cannot_leave", lang))

    db.delete(membership)
    db.commit()
    return None


@router.get("/{team_id}/members", response_model=list[TeamMemberOut])
def list_team_members(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> list[TeamMemberOut]:
    """docs/frontend-to-backend-requests.md #5: 팀 소속 멤버만 조회 가능하도록 권한 체크."""
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("team_not_found", lang))

    requester_membership = (
        db.query(TeamMembership)
        .filter(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id)
        .first()
    )
    if requester_membership is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, t("team_members_only", lang))

    refresh_unconfirmed_assignments(db, team_id)

    rows = (
        db.query(User, TeamMembership)
        .join(TeamMembership, TeamMembership.user_id == User.id)
        .filter(TeamMembership.team_id == team_id)
        .all()
    )
    return [
        TeamMemberOut(
            user_id=user.id,
            name=user.name,
            github_handle=user.github_handle,
            role=membership.role,
            job_role=membership.job_role,
            assigned_area=membership.assigned_area,
            assigned_paths=membership.assigned_paths,
            assigned_area_confirmed=membership.assigned_area_confirmed,
        )
        for user, membership in rows
    ]


@router.patch("/{team_id}/members/me", response_model=TeamMemberOut)
def update_my_assignment(
    team_id: str,
    payload: MyAssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> TeamMemberOut:
    """기능명세서 4.2: 본인의 역할·담당 영역을 직접 입력·수정한다. 제출한 값은 이후
    자동 추론이 덮어쓰지 않는다 (assigned_area_confirmed=True로 전환)."""
    membership = (
        db.query(TeamMembership)
        .filter(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id)
        .first()
    )
    if membership is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("not_team_member", lang))

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(membership, field, value)
    membership.assigned_area_confirmed = True
    db.commit()
    db.refresh(membership)

    return TeamMemberOut(
        user_id=current_user.id,
        name=current_user.name,
        github_handle=current_user.github_handle,
        role=membership.role,
        job_role=membership.job_role,
        assigned_area=membership.assigned_area,
        assigned_paths=membership.assigned_paths,
        assigned_area_confirmed=membership.assigned_area_confirmed,
    )
