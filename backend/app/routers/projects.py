from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user, require_project_admin
from app.core.i18n import get_lang, t
from app.models.closure import ClosureRun
from app.models.github_event import RawEvent
from app.models.project import Project, ProjectAdmin, ProjectDocument, ProjectRepo, ProjectTeam
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
from app.services import document_extractor

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> ProjectOut:
    """O-003: 프로젝트 생성 및 레포 선택. 생성자의 팀이 첫 참여 팀이 되고,
    생성자는 프로젝트 관리자가 된다.

    docs/frontend-to-backend-requests.md #8: team_id는 선택 입력이다. 아직 소속 팀이 없는
    사용자도 프로젝트만 먼저 만들고, 참여 팀은 POST /projects/{id}/teams로 나중에 추가할 수 있다."""
    team = None
    if payload.team_id is not None:
        team = db.get(Team, payload.team_id)
        if team is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, t("team_not_found", lang))

    project = Project(name=payload.name)
    db.add(project)
    db.flush()

    if team is not None:
        db.add(ProjectTeam(project_id=project.id, team_id=team.id))
    db.add(ProjectAdmin(project_id=project.id, user_id=current_user.id))
    db.commit()
    db.refresh(project)
    return ProjectOut(
        id=project.id,
        name=project.name,
        created_at=project.created_at,
        is_admin=True,
    )


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
    lang: str = Depends(get_lang),
) -> ProjectOut:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("project_not_found", lang))

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
        created_at=project.created_at,
        is_admin=is_admin,
    )


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> ProjectOut:
    """C-003: 프로젝트 설정 수정 (이름). 레포 변경은 실제 접근 권한 재검증이 필요하므로
    이 엔드포인트가 아니라 /github/connect를 통해서만 한다."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("project_not_found", lang))
    require_project_admin(db, project_id, current_user, lang)

    project.name = payload.name
    db.commit()
    db.refresh(project)
    # require_project_admin이 이미 검증했으므로 is_admin=True. 이걸 안 채우면 Project에는
    # is_admin 속성이 없어 ProjectOut 기본값(False)으로 응답돼, 방금 검증된 관리자에게도
    # is_admin=false가 내려간다 (O-003 생성 응답과 동일한 문제).
    return ProjectOut(
        id=project.id,
        name=project.name,
        created_at=project.created_at,
        is_admin=True,
    )


@router.get("/{project_id}/document", response_model=ProjectDocumentOut)
def get_project_document(project_id: str, db: Session = Depends(get_db)) -> ProjectDocument:
    """저장된 기획 문서를 조회한다. 저장 후 재조회로 저장 여부를 확인할 수 있게 한다."""
    if db.get(Project, project_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "프로젝트를 찾을 수 없습니다.")

    doc = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id).first()
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "저장된 기획 문서가 없습니다.")
    return doc


@router.put("/{project_id}/document", response_model=ProjectDocumentOut)
def upsert_project_document(
    project_id: str,
    payload: ProjectDocumentIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> ProjectDocument:
    """O-004: 기획안·정리 문서를 텍스트로 저장해 AI 컨텍스트로 사용한다. 별도 분석 없음."""
    if db.get(Project, project_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("project_not_found", lang))

    doc = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id).first()
    if doc is None:
        doc = ProjectDocument(project_id=project_id, content=payload.content)
        db.add(doc)
    else:
        doc.content = payload.content
        doc.source_filename = None  # 텍스트로 직접 덮어쓰면 이전 업로드 파일명 표시는 더 이상 안 맞다
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/{project_id}/document/upload", response_model=ProjectDocumentOut)
async def upload_project_document(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> ProjectDocument:
    """docs/frontend-to-backend-requests.md #14: 기획 문서를 파일(PDF/DOCX/PPTX/TXT/MD)로
    업로드하면 서버가 텍스트를 추출해 PUT과 동일한 project_documents.content에 저장한다.
    원본 파일 자체는 저장하지 않고 추출된 텍스트만 남긴다."""
    if db.get(Project, project_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("project_not_found", lang))

    data = await file.read()
    if len(data) > document_extractor.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            t(
                "document_file_too_large",
                lang,
                max_mb=document_extractor.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024),
            ),
        )

    try:
        content = document_extractor.extract_text(file.filename or "", data)
    except document_extractor.DocumentExtractionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    doc = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id).first()
    if doc is None:
        doc = ProjectDocument(project_id=project_id, content=content, source_filename=file.filename)
        db.add(doc)
    else:
        doc.content = content
        doc.source_filename = file.filename
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/{project_id}/teams", status_code=status.HTTP_204_NO_CONTENT)
def add_participating_team(
    project_id: str,
    payload: AddParticipatingTeamRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> None:
    """O-006: 프로젝트 관리자가 다른 팀을 참여 팀으로 추가한다 (Border 04 대응)."""
    if db.get(Project, project_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("project_not_found", lang))
    if db.get(Team, payload.team_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("team_not_found", lang))
    require_project_admin(db, project_id, current_user, lang)

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
def list_participating_teams(
    project_id: str, db: Session = Depends(get_db), lang: str = Depends(get_lang)
) -> list[Team]:
    """docs/frontend-to-backend-requests.md #6: 이 프로젝트에 참여 중인 팀 목록."""
    if db.get(Project, project_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("project_not_found", lang))

    return (
        db.query(Team)
        .join(ProjectTeam, ProjectTeam.team_id == Team.id)
        .filter(ProjectTeam.project_id == project_id)
        .all()
    )


@router.delete("/{project_id}/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_participating_team(
    project_id: str,
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> None:
    """docs/frontend-to-backend-requests.md #12: 프로젝트 관리자가 참여 팀을 내보낸다.
    프로젝트 삭제(#3)와 달리 팀·프로젝트 자체를 지우는 게 아니라 참여 관계만 끊는 것이므로,
    그 팀이 남긴 closure_runs/summary_cards(과거 타임라인 기록)는 지우지 않고 그대로 둔다."""
    if db.get(Project, project_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("project_not_found", lang))
    if db.get(Team, team_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("team_not_found", lang))
    require_project_admin(db, project_id, current_user, lang)

    db.query(ProjectTeam).filter(
        ProjectTeam.project_id == project_id, ProjectTeam.team_id == team_id
    ).delete(synchronize_session=False)
    db.commit()
    return None


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> None:
    """docs/frontend-to-backend-requests.md #3: 프로젝트 관리자만 가능. project_teams·
    project_admins·project_documents·closure_runs/summary_cards·raw_events까지 모두 cascade 삭제."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("project_not_found", lang))
    require_project_admin(db, project_id, current_user, lang)

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
    db.query(ProjectRepo).filter(ProjectRepo.project_id == project_id).delete(synchronize_session=False)

    db.delete(project)
    db.commit()
    return None
