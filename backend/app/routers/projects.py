from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.project import Project, ProjectAdmin, ProjectDocument, ProjectTeam
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

router = APIRouter(prefix="/projects", tags=["projects"])


def _require_project_admin(db: Session, project_id, user: User) -> None:
    admin = (
        db.query(ProjectAdmin)
        .filter(ProjectAdmin.project_id == project_id, ProjectAdmin.user_id == user.id)
        .first()
    )
    if admin is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "프로젝트 관리자만 수행할 수 있습니다.")


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
def get_project(project_id: str, db: Session = Depends(get_db)) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "프로젝트를 찾을 수 없습니다.")
    return project


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
    _require_project_admin(db, project_id, current_user)

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
    _require_project_admin(db, project_id, current_user)

    exists = (
        db.query(ProjectTeam)
        .filter(ProjectTeam.project_id == project_id, ProjectTeam.team_id == payload.team_id)
        .first()
    )
    if exists is None:
        db.add(ProjectTeam(project_id=project_id, team_id=payload.team_id))
        db.commit()
    return None
