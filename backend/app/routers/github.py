import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_project_admin
from app.core.i18n import get_lang, t
from app.models.project import Project, ProjectRepo
from app.models.user import User
from app.schemas.github import GithubConnectRequest, GithubConnectResult, GithubRepoStatusOut
from app.services import github_client, github_collector
from app.services.unanswered_service import detect_unanswered_items

router = APIRouter(prefix="/projects/{project_id}/github", tags=["github"])


@router.post("/connect", response_model=GithubConnectResult)
def connect_repo(
    project_id: str,
    payload: GithubConnectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> GithubConnectResult:
    """G-001: 레포 연결 및 검증.

    docs/frontend-to-backend-requests.md #11: 프로젝트당 레포를 여러 개 연결할 수 있다.
    연결을 요청한 사용자의 GitHub 토큰으로 레포 접근 권한을 실제로 검증하고, 성공하면
    그 자리에서 직전 3일 소급 수집(G-002)까지 수행한다. 이미 연결된 레포를 다시 연결하면
    재시도로 취급해 소급 수집을 다시 실행한다(예: 이전 시도가 실패했을 때)."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("project_not_found", lang))
    if not current_user.github_access_token:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, t("github_login_required", lang))

    with httpx.Client(timeout=10) as client:
        try:
            repo = github_client.get_repo(client, current_user.github_access_token, payload.repo_full_name)
        except github_client.GithubApiError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    repo_id = str(repo["id"])
    project_repo = (
        db.query(ProjectRepo)
        .filter(ProjectRepo.project_id == project_id, ProjectRepo.repo_id == repo_id)
        .first()
    )
    if project_repo is None:
        project_repo = ProjectRepo(
            project_id=project_id,
            repo_full_name=payload.repo_full_name,
            repo_id=repo_id,
            connected_by_user_id=current_user.id,
        )
        db.add(project_repo)
    else:
        project_repo.repo_full_name = payload.repo_full_name
        project_repo.connected_by_user_id = current_user.id
        project_repo.gh_last_collected_at = None  # G-002: 다음 수집이 직전 3일 소급으로 동작
        project_repo.gh_last_error = None
    db.commit()
    db.refresh(project_repo)

    try:
        backfill_count = github_collector.collect_repo_events(db, project_repo)
    except github_collector.CollectionError as exc:
        prefix = "레포는 연결됐지만 소급 수집에 실패했습니다" if lang == "ko" else "Repo connected, but backfill failed"
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"{prefix}: {exc}")

    detect_unanswered_items(db, project)  # 3.3: 수집 직후 미응답 항목 갱신

    return GithubConnectResult(
        project_id=project.id,
        connected=True,
        repo_id=project_repo.repo_id,
        repo_full_name=project_repo.repo_full_name,
        backfill_event_count=backfill_count,
    )


@router.get("/status", response_model=list[GithubRepoStatusOut])
def github_status(
    project_id: str, db: Session = Depends(get_db), lang: str = Depends(get_lang)
) -> list[GithubRepoStatusOut]:
    """G-006: 연결된 레포마다 마지막 수집 시각과 실패 여부 표시."""
    if db.get(Project, project_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("project_not_found", lang))

    repos = db.query(ProjectRepo).filter(ProjectRepo.project_id == project_id).all()
    return [
        GithubRepoStatusOut(
            repo_id=repo.repo_id,
            repo_full_name=repo.repo_full_name,
            last_collected_at=repo.gh_last_collected_at,
            last_error=repo.gh_last_error,
        )
        for repo in repos
    ]


@router.delete("/repos/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_repo(
    project_id: str,
    repo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> None:
    """docs/frontend-to-backend-requests.md #11: 프로젝트 관리자가 연결된 레포를 하나
    해제한다. raw_events에는 레포별 귀속이 없어(이 요청 범위 밖) 이미 수집된 활동 기록은
    지우지 않는다 — 앞으로의 수집만 멈춘다."""
    if db.get(Project, project_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("project_not_found", lang))
    require_project_admin(db, project_id, current_user, lang)

    project_repo = (
        db.query(ProjectRepo)
        .filter(ProjectRepo.project_id == project_id, ProjectRepo.repo_id == repo_id)
        .first()
    )
    if project_repo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("repo_not_connected", lang))

    db.delete(project_repo)
    db.commit()
    return None
