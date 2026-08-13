from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.closure import ClosureRun, ClosureTrigger
from app.models.github_event import RawEvent
from app.models.project import Project, ProjectTeam
from app.models.summary import CardStatus, SummaryCard
from app.models.team import Team

NO_CHANGE_TEXT = {"ko": "변동 없음", "en": "No changes"}


def _participating_languages(db: Session, project_id) -> list[str]:
    languages = (
        db.execute(
            select(Team.default_language)
            .join(ProjectTeam, ProjectTeam.team_id == Team.id)
            .where(ProjectTeam.project_id == project_id)
            .distinct()
        )
        .scalars()
        .all()
    )
    return list(languages) or ["ko"]


def build_closure_run(
    db: Session,
    project: Project,
    team: Team,
    trigger_type: ClosureTrigger,
    range_start: datetime,
    range_end: datetime,
) -> ClosureRun:
    """주어진 [range_start, range_end) 구간으로 마감 1건을 생성한다. 이벤트가 없으면
    '변동 없음' 카드를 생성한다 (S-006, back 담당). 이벤트가 있으면 언어별 카드를
    content=NULL로 만들어두고, AI 파트가 S-004·S-005로 채우도록 한다 (2단계 연동 계약).
    자동/수동 마감(run_closure)과 데모 시드(D-001)의 과거 구간 생성이 공유하는 핵심 로직."""
    closure_run = ClosureRun(
        project_id=project.id,
        team_id=team.id,
        trigger_type=trigger_type,
        range_start=range_start,
        range_end=range_end,
    )
    db.add(closure_run)
    db.flush()

    has_events = (
        db.query(RawEvent.id)
        .filter(
            RawEvent.project_id == project.id,
            RawEvent.team_id == team.id,
            RawEvent.gh_created_at >= range_start,
            RawEvent.gh_created_at < range_end,
        )
        .first()
        is not None
    )

    for language in _participating_languages(db, project.id):
        if has_events:
            card = SummaryCard(
                closure_run_id=closure_run.id,
                language=language,
                content=None,
                status=CardStatus.NORMAL,
            )
        else:
            card = SummaryCard(
                closure_run_id=closure_run.id,
                language=language,
                content=NO_CHANGE_TEXT.get(language, NO_CHANGE_TEXT["en"]),
                status=CardStatus.NO_CHANGE,
            )
        db.add(card)

    db.flush()
    return closure_run


def run_closure(
    db: Session,
    project: Project,
    team: Team,
    trigger_type: ClosureTrigger,
    now: datetime | None = None,
) -> ClosureRun:
    """S-001~003: 1 마감 실행 = 1 카드. 범위는 직전 마감 시각 이후 ~ 현재로, 겹치지 않는다.

    `now`는 자동 마감 워커가 시간 시뮬레이션(D-003) 값을 주입할 때 쓴다. 수동 마감(S-002)은
    항상 실제 시각을 쓰므로 인자를 생략한다."""
    last_run = (
        db.query(ClosureRun)
        .filter(ClosureRun.project_id == project.id, ClosureRun.team_id == team.id)
        .order_by(ClosureRun.range_end.desc())
        .first()
    )
    range_start = last_run.range_end if last_run else project.created_at
    range_end = now or datetime.now(timezone.utc)

    closure_run = build_closure_run(db, project, team, trigger_type, range_start, range_end)
    db.commit()
    db.refresh(closure_run)
    return closure_run


def _today_work_end_boundary_utc(team: Team, effective_now: datetime) -> datetime:
    team_tz = ZoneInfo(team.timezone)
    local_now = effective_now.astimezone(team_tz)
    boundary_local = local_now.replace(
        hour=team.work_end.hour, minute=team.work_end.minute, second=0, microsecond=0
    )
    return boundary_local.astimezone(timezone.utc)


def should_auto_close(db: Session, project: Project, team: Team, effective_now: datetime) -> bool:
    """S-001: 팀의 로컬 업무 종료 시각을 지났고, 그 경계 이후로 아직 마감된 적이 없으면 True."""
    team_tz = ZoneInfo(team.timezone)
    local_now = effective_now.astimezone(team_tz)
    if local_now.time() < team.work_end:
        return False

    boundary_utc = _today_work_end_boundary_utc(team, effective_now)

    last_run = (
        db.query(ClosureRun)
        .filter(ClosureRun.project_id == project.id, ClosureRun.team_id == team.id)
        .order_by(ClosureRun.range_end.desc())
        .first()
    )
    return last_run is None or last_run.range_end < boundary_utc
