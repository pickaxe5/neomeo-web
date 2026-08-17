"""G-002~005: GitHub에서 변경사항을 수집해 0층(raw_events)에 정규화·저장한다.

PR·이슈는 "생성"과 "머지/종료"를 각각 별도의 불변 사실 이벤트로 기록한다 (0층은 구조화 사실
데이터이므로, 상태가 바뀌는 하나의 행을 UPDATE하기보다 "PR #5가 t1에 열렸다"/"PR #5가 t2에
머지됐다"는 두 개의 사실을 남기는 편이 근거 표기(L-004)와 재수집 시 중복 방지에 더 안전하다).
"""

import uuid
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.github_event import EventType, RawEvent
from app.models.project import Project, ProjectRepo, ProjectTeam
from app.models.team import TeamMembership
from app.models.user import User
from app.services import github_client

BACKFILL_WINDOW_DAYS = 3
COMMIT_FETCH_LIMIT = 20


class CollectionError(Exception):
    pass


def _get_token(db: Session, project_repo: ProjectRepo) -> str:
    user = db.get(User, project_repo.connected_by_user_id)
    if user is None or not user.github_access_token:
        raise CollectionError("연동 계정에 GitHub 토큰이 없습니다. GitHub 로그인이 필요합니다.")
    return user.github_access_token


def _attribute_team(db: Session, project_id: uuid.UUID, actor_handle: str | None) -> uuid.UUID | None:
    """G-004: GitHub 핸들 → 유저 → (이 프로젝트 참여 팀 중) 소속 팀으로 귀속한다."""
    if not actor_handle:
        return None
    user = db.query(User).filter(User.github_handle == actor_handle).first()
    if user is None:
        return None
    membership = (
        db.query(TeamMembership)
        .join(ProjectTeam, ProjectTeam.team_id == TeamMembership.team_id)
        .filter(ProjectTeam.project_id == project_id, TeamMembership.user_id == user.id)
        .first()
    )
    return membership.team_id if membership else None


def _existing_github_ids(db: Session, project_id: uuid.UUID, event_type: EventType) -> set[str]:
    rows = db.execute(
        select(RawEvent.github_id).where(RawEvent.project_id == project_id, RawEvent.type == event_type)
    ).scalars()
    return set(rows)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _build_pr_events(
    project_id: uuid.UUID, repo_id: str, db: Session, prs: list[dict], existing_ids: set[str]
) -> list[RawEvent]:
    events: list[RawEvent] = []
    for pr in prs:
        number = pr["number"]
        actor = pr.get("user", {}).get("login")
        base_kwargs = dict(
            project_id=project_id,
            type=EventType.PR,
            actor_handle=actor,
            title=pr.get("title"),
            body=pr.get("body"),
            url=pr.get("html_url"),
            raw_payload=pr,
        )

        # github_id는 repo_id를 접두어로 붙인다 — PR·이슈 번호는 레포 안에서만 유일해서,
        # 프로젝트에 레포가 여러 개 연결되면 서로 다른 레포의 "PR #1"이 충돌할 수 있다.
        created_id = f"{repo_id}:pr:{number}:created"
        if created_id not in existing_ids:
            events.append(
                RawEvent(
                    **base_kwargs,
                    github_id=created_id,
                    state="open",
                    gh_created_at=_parse_dt(pr.get("created_at")),
                    team_id=_attribute_team(db, project_id, actor),
                )
            )

        merged_at = pr.get("merged_at")
        merged_id = f"{repo_id}:pr:{number}:merged"
        if merged_at and merged_id not in existing_ids:
            events.append(
                RawEvent(
                    **base_kwargs,
                    github_id=merged_id,
                    state="merged",
                    gh_created_at=_parse_dt(merged_at),
                    gh_closed_at=_parse_dt(merged_at),
                    team_id=_attribute_team(db, project_id, actor),
                )
            )
    return events


def _build_issue_events(
    project_id: uuid.UUID, repo_id: str, db: Session, issues: list[dict], existing_ids: set[str]
) -> list[RawEvent]:
    events: list[RawEvent] = []
    for issue in issues:
        number = issue["number"]
        actor = issue.get("user", {}).get("login")
        base_kwargs = dict(
            project_id=project_id,
            type=EventType.ISSUE,
            actor_handle=actor,
            title=issue.get("title"),
            body=issue.get("body"),
            url=issue.get("html_url"),
            raw_payload=issue,
        )

        created_id = f"{repo_id}:issue:{number}:created"
        if created_id not in existing_ids:
            events.append(
                RawEvent(
                    **base_kwargs,
                    github_id=created_id,
                    state="open",
                    gh_created_at=_parse_dt(issue.get("created_at")),
                    team_id=_attribute_team(db, project_id, actor),
                )
            )

        closed_at = issue.get("closed_at")
        closed_id = f"{repo_id}:issue:{number}:closed"
        if closed_at and closed_id not in existing_ids:
            events.append(
                RawEvent(
                    **base_kwargs,
                    github_id=closed_id,
                    state="closed",
                    gh_created_at=_parse_dt(closed_at),
                    gh_closed_at=_parse_dt(closed_at),
                    team_id=_attribute_team(db, project_id, actor),
                )
            )
    return events


def _build_review_comment_events(
    project_id: uuid.UUID, repo_id: str, db: Session, comments: list[dict], existing_ids: set[str]
) -> list[RawEvent]:
    events: list[RawEvent] = []
    for comment in comments:
        github_id = f"{repo_id}:review_comment:{comment['id']}"
        if github_id in existing_ids:
            continue
        actor = comment.get("user", {}).get("login")
        events.append(
            RawEvent(
                project_id=project_id,
                type=EventType.REVIEW_COMMENT,
                github_id=github_id,
                actor_handle=actor,
                title=None,
                body=comment.get("body"),
                url=comment.get("html_url"),
                state=None,
                gh_created_at=_parse_dt(comment.get("created_at")),
                raw_payload=comment,
                team_id=_attribute_team(db, project_id, actor),
            )
        )
    return events


def _build_commit_events(
    client: httpx.Client,
    token: str,
    full_name: str,
    project_id: uuid.UUID,
    repo_id: str,
    db: Session,
    commits: list[dict],
    existing_ids: set[str],
) -> list[RawEvent]:
    events: list[RawEvent] = []
    for commit in commits[:COMMIT_FETCH_LIMIT]:
        sha = commit["sha"]
        github_id = f"{repo_id}:commit:{sha}"
        if github_id in existing_ids:
            continue
        actor = (commit.get("author") or {}).get("login")
        commit_info = commit.get("commit", {})
        message = commit_info.get("message", "")
        title = message.splitlines()[0] if message else None
        try:
            file_paths = github_client.get_commit_files(client, token, full_name, sha)
        except github_client.GithubApiError:
            file_paths = None

        events.append(
            RawEvent(
                project_id=project_id,
                type=EventType.COMMIT,
                github_id=github_id,
                actor_handle=actor,
                title=title,
                body=None,
                url=commit.get("html_url"),
                state=None,
                file_paths=file_paths,
                gh_created_at=_parse_dt(commit_info.get("author", {}).get("date")),
                raw_payload=commit,
                team_id=_attribute_team(db, project_id, actor),
            )
        )
    return events


def collect_repo_events(db: Session, project_repo: ProjectRepo) -> int:
    """레포 1건에 대해 PR·이슈·리뷰코멘트·커밋을 수집해 저장한다. 반환값은 새로 저장된 건수.
    실패 시 project_repo.gh_last_error에 사유를 남기고 CollectionError를 올린다."""
    try:
        token = _get_token(db, project_repo)
        since = project_repo.gh_last_collected_at or (
            datetime.now(timezone.utc) - timedelta(days=BACKFILL_WINDOW_DAYS)
        )
        project_id = project_repo.project_id
        repo_id = project_repo.repo_id

        with httpx.Client(timeout=15) as client:
            prs = github_client.list_pull_requests(client, token, project_repo.repo_full_name, since)
            issues = github_client.list_issues(client, token, project_repo.repo_full_name, since)
            comments = github_client.list_review_comments(client, token, project_repo.repo_full_name, since)
            commits = github_client.list_commits(client, token, project_repo.repo_full_name, since)

            new_events: list[RawEvent] = []
            new_events += _build_pr_events(
                project_id, repo_id, db, prs, _existing_github_ids(db, project_id, EventType.PR)
            )
            new_events += _build_issue_events(
                project_id, repo_id, db, issues, _existing_github_ids(db, project_id, EventType.ISSUE)
            )
            new_events += _build_review_comment_events(
                project_id,
                repo_id,
                db,
                comments,
                _existing_github_ids(db, project_id, EventType.REVIEW_COMMENT),
            )
            new_events += _build_commit_events(
                client,
                token,
                project_repo.repo_full_name,
                project_id,
                repo_id,
                db,
                commits,
                _existing_github_ids(db, project_id, EventType.COMMIT),
            )

        for event in new_events:
            db.add(event)

        project_repo.gh_last_collected_at = datetime.now(timezone.utc)
        project_repo.gh_last_error = None
        db.commit()
        return len(new_events)

    except (CollectionError, github_client.GithubApiError) as exc:
        db.rollback()
        project_repo.gh_last_error = str(exc)
        db.commit()
        raise CollectionError(str(exc)) from exc


def collect_project_events(db: Session, project: Project) -> int:
    """docs/frontend-to-backend-requests.md #11: 프로젝트에 연결된 모든 레포를 순회하며
    수집한다. 레포 하나가 실패해도(개별 gh_last_error에 남음) 나머지 레포 수집은 계속한다.
    반환값은 전체 신규 이벤트 수. 연결된 레포가 하나도 없으면 CollectionError."""
    repos = db.query(ProjectRepo).filter(ProjectRepo.project_id == project.id).all()
    if not repos:
        raise CollectionError("연동된 레포가 없습니다.")

    total = 0
    for repo in repos:
        try:
            total += collect_repo_events(db, repo)
        except CollectionError:
            continue
    return total
