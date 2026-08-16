import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.i18n import get_lang, t
from app.models.project import Project
from app.models.user import User
from app.schemas.github import GithubConnectRequest, GithubConnectResult, GithubStatusOut
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
    """G-001: 레포 연결 및 검증. 프로젝트당 레포 1개.

    연결을 요청한 사용자의 GitHub 토큰으로 레포 접근 권한을 실제로 검증하고, 성공하면
    그 자리에서 직전 3일 소급 수집(G-002)까지 수행한다."""
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

    project.repo_full_name = payload.repo_full_name
    project.repo_id = str(repo["id"])
    project.github_connected_by_user_id = current_user.id
    project.gh_last_collected_at = None  # G-002: 다음 수집이 직전 3일 소급으로 동작하도록 초기화
    project.gh_last_error = None
    db.commit()

    try:
        backfill_count = github_collector.collect_project_events(db, project)
    except github_collector.CollectionError as exc:
        prefix = "레포는 연결됐지만 소급 수집에 실패했습니다" if lang == "ko" else "Repo connected, but backfill failed"
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"{prefix}: {exc}")

    detect_unanswered_items(db, project)  # 3.3: 수집 직후 미응답 항목 갱신

    return GithubConnectResult(
        project_id=project.id,
        connected=True,
        repo_id=project.repo_id,
        backfill_event_count=backfill_count,
    )


@router.get("/status", response_model=GithubStatusOut)
def github_status(
    project_id: str, db: Session = Depends(get_db), lang: str = Depends(get_lang)
) -> GithubStatusOut:
    """G-006: 마지막 수집 시각과 실패 여부 표시."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("project_not_found", lang))

    return GithubStatusOut(
        project_id=project.id,
        connected=bool(project.repo_full_name),
        last_collected_at=project.gh_last_collected_at,
        last_error=project.gh_last_error,
    )
