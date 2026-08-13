"""기능명세서 4.2: 역할·담당 영역 자동 추론. 커밋의 변경 파일 경로를 집계해 팀원이 주로
건드리는 디렉토리를 추정한다. 사용자가 직접 입력·확인한 값(assigned_area_confirmed=True)은
이후 추론이 덮어쓰지 않는다 — "직접 입력한 값이 자동 추론 결과보다 우선한다" 원칙."""

from collections import Counter

from sqlalchemy.orm import Session

from app.models.github_event import EventType, RawEvent
from app.models.project import ProjectTeam
from app.models.team import TeamMembership
from app.models.user import User

MIN_COMMITS_FOR_INFERENCE = 3
MIN_TOP_DIR_SHARE = 0.3
MAX_INFERRED_PATHS = 3


def _top_level_dir(path: str) -> str:
    return path.split("/", 1)[0] if "/" in path else path


def infer_assigned_paths(db: Session, team_id, user: User) -> list[str] | None:
    """이 팀이 참여 중인 프로젝트들에서 user의 커밋 변경 파일 경로를 집계해 주요 디렉토리를
    추정한다. 활동 이력이 너무 적거나(MIN_COMMITS_FOR_INFERENCE 미만 커밋) 경로가 너무
    분산되어 있으면(상위 디렉토리 비중이 MIN_TOP_DIR_SHARE 미만) None을 반환해 "미설정"으로 둔다."""
    if not user.github_handle:
        return None

    rows = (
        db.query(RawEvent.file_paths)
        .join(ProjectTeam, ProjectTeam.project_id == RawEvent.project_id)
        .filter(
            ProjectTeam.team_id == team_id,
            RawEvent.type == EventType.COMMIT,
            RawEvent.actor_handle == user.github_handle,
            RawEvent.file_paths.isnot(None),
        )
        .all()
    )
    if len(rows) < MIN_COMMITS_FOR_INFERENCE:
        return None

    counter: Counter[str] = Counter()
    for (file_paths,) in rows:
        for path in file_paths or []:
            counter[_top_level_dir(path)] += 1

    total = sum(counter.values())
    if total == 0:
        return None

    ranked = counter.most_common(MAX_INFERRED_PATHS)
    top_share = ranked[0][1] / total
    if top_share < MIN_TOP_DIR_SHARE:
        return None

    return [directory for directory, _ in ranked]


def refresh_unconfirmed_assignments(db: Session, team_id) -> None:
    """확정되지 않은 팀원들의 assigned_paths를 최신 활동 기준으로 다시 계산해 갱신한다.
    GET /teams/{id}/members 조회 시점마다 호출되는 조회-시 재계산 방식이라, 별도의
    백그라운드 트리거 없이도 "활동이 누적되면 추론이 갱신된다"는 요구를 만족한다."""
    memberships = (
        db.query(TeamMembership)
        .filter(TeamMembership.team_id == team_id, TeamMembership.assigned_area_confirmed.is_(False))
        .all()
    )
    for membership in memberships:
        user = db.get(User, membership.user_id)
        if user is None:
            continue
        membership.assigned_paths = infer_assigned_paths(db, team_id, user)
    db.commit()
