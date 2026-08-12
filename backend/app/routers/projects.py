from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user, require_project_admin
from app.models.closure import ClosureRun
from app.models.github_event import RawEvent
from app.models.project import Project, ProjectAdmin, ProjectDocument, ProjectTeam
from app.models.summary import SummaryCard
from app.models.team import Team
from app.models.user import User
from app.schemas.project import (
    AddParticipatingTeamRequest,
    ProjectCreate,
    ProjectDocumentIn,
    ProjectDocumentOut,
    ProjectOut,
    ProjectUpdate,
)
from app.schemas.team import TeamOut

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    """O-003: 프로젝트 생성 및 레포 선택. 생성자의 팀이 첫 참여 팀이 되고,
    생성자는 프로젝트 관리자가 된다."""
    team = db.get(Team, payload.team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "팀을 찾을 수 없습니다.")

    project = Project(
        name=payload.name,
        repo_full_name=payload.repo_full_name,
        repo_id=payload.repo_id,
    )
    db.add(project)
    db.flush()

    db.add(ProjectTeam(project_id=project.id, team_id=team.id))
    db.add(ProjectAdmin(project_id=project.id, user_id=current_user.id))
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
) -> ProjectOut:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "프로젝트를 찾을 수 없습니다.")

    is_admin = False
    if current_user is not None:
        is_admin = (
            db.query(ProjectAdmin)
            .filter(ProjectAdmin.project_id == project_id, ProjectAdmin.user_id == current_user.id)
            .first()
            is not None
        )
    return ProjectOut(
        id=project.id,
        name=project.name,
        repo_full_name=project.repo_full_name,
        repo_id=project.repo_id,
        created_at=project.created_at,
        is_admin=is_admin,
    )


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    """C-003: 프로젝트 설정 수정 (이름). 레포 변경은 실제 접근 권한 재검증이 필요하므로
    이 엔드포인트가 아니라 /github/connect를 통해서만 한다."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "프로젝트를 찾을 수 없습니다.")
    require_project_admin(db, project_id, current_user)

    project.name = payload.name
    db.commit()
    db.refresh(project)
    return project


@router.put("/{project_id}/document", response_model=ProjectDocumentOut)
def upsert_project_document(
    project_id: str,
    payload: ProjectDocumentIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectDocument:
    """O-004: 기획안·정리 문서를 텍스트로 저장해 AI 컨텍스트로 사용한다. 별도 분석 없음."""
    if db.get(Project, project_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "프로젝트를 찾을 수 없습니다.")

    doc = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id).first()
    if doc is None:
        doc = ProjectDocument(project_id=project_id, content=payload.content)
        db.add(doc)
    else:
        doc.content = payload.content
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/{project_id}/teams", status_code=status.HTTP_204_NO_CONTENT)
def add_participating_team(
    project_id: str,
    payload: AddParticipatingTeamRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """O-006: 프로젝트 관리자가 다른 팀을 참여 팀으로 추가한다 (Border 04 대응)."""
    if db.get(Project, project_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "프로젝트를 찾을 수 없습니다.")
    if db.get(Team, payload.team_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "팀을 찾을 수 없습니다.")
    require_project_admin(db, project_id, current_user)

    exists = (
        db.query(ProjectTeam)
        .filter(ProjectTeam.project_id == project_id, ProjectTeam.team_id == payload.team_id)
        .first()
    )
    if exists is None:
        db.add(ProjectTeam(project_id=project_id, team_id=payload.team_id))
        db.commit()
    return None


@router.get("/{project_id}/teams", response_model=list[TeamOut])
def list_participating_teams(project_id: str, db: Session = Depends(get_db)) -> list[Team]:
    """docs/frontend-to-backend-requests.md #6: 이 프로젝트에 참여 중인 팀 목록."""
    if db.get(Project, project_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "프로젝트를 찾을 수 없습니다.")

    return (
        db.query(Team)
        .join(ProjectTeam, ProjectTeam.team_id == Team.id)
        .filter(ProjectTeam.project_id == project_id)
        .all()
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """docs/frontend-to-backend-requests.md #3: 프로젝트 관리자만 가능. project_teams·
    project_admins·project_documents·closure_runs/summary_cards·raw_events까지 모두 cascade 삭제."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "프로젝트를 찾을 수 없습니다.")
    require_project_admin(db, project_id, current_user)

    closure_run_ids = [
        row[0] for row in db.query(ClosureRun.id).filter(ClosureRun.project_id == project_id).all()
    ]
    if closure_run_ids:
        db.query(SummaryCard).filter(SummaryCard.closure_run_id.in_(closure_run_ids)).delete(
            synchronize_session=False
        )
        db.query(ClosureRun).filter(ClosureRun.project_id == project_id).delete(synchronize_session=False)

    db.query(RawEvent).filter(RawEvent.project_id == project_id).delete(synchronize_session=False)
    db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id).delete(synchronize_session=False)
    db.query(ProjectAdmin).filter(ProjectAdmin.project_id == project_id).delete(synchronize_session=False)
    db.query(ProjectTeam).filter(ProjectTeam.project_id == project_id).delete(synchronize_session=False)

    db.delete(project)
    db.commit()
    return None
