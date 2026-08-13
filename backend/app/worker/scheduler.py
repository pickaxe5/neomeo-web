"""S-001: 10분 폴링 워커. 정시 보장이 필요 없다는 원문서 원칙(오차 10분 허용)에 따라
별도 워커 프로세스·큐 인프라 없이 FastAPI 프로세스 안에서 APScheduler로 돈다.

주의: 단일 uvicorn 워커 프로세스를 전제로 한다. `--workers N`으로 여러 프로세스를 띄우면
이 잡이 N번 중복 실행된다 — 분산 락은 해커톤 범위 밖("정교하게 만들지 말 것")으로 둔다.
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.closure import ClosureTrigger
from app.models.project import Project, ProjectTeam
from app.models.team import Team
from app.services import github_collector
from app.services.closure_service import run_closure, should_auto_close

logger = logging.getLogger("neomeo.worker")


def _effective_now(project: Project) -> datetime:
    """D-003: 시뮬레이션 시각이 설정돼 있으면 그것을 "지금"으로 취급한다."""
    return project.simulated_now or datetime.now(timezone.utc)


def _poll_project(db: Session, project: Project) -> None:
    try:
        github_collector.collect_project_events(db, project)
    except github_collector.CollectionError as exc:
        logger.warning("GitHub 수집 실패 (project=%s): %s", project.id, exc)

    effective_now = _effective_now(project)
    teams = (
        db.query(Team)
        .join(ProjectTeam, ProjectTeam.team_id == Team.id)
        .filter(ProjectTeam.project_id == project.id)
        .all()
    )
    for team in teams:
        if should_auto_close(db, project, team, effective_now):
            run_closure(db, project, team, ClosureTrigger.AUTO, now=effective_now)


def poll_all_projects() -> None:
    db = SessionLocal()
    try:
        projects = db.query(Project).filter(Project.repo_full_name.isnot(None)).all()
        for project in projects:
            _poll_project(db, project)
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        poll_all_projects,
        "interval",
        minutes=settings.poll_interval_minutes,
        id="poll_all_projects",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler
