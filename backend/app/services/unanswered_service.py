"""기능명세서 3.3: 아직 답을 받지 못한 질문·리뷰 요청 식별. 명시적 신호(리뷰어 지정, @멘션)를
우선 사용하고, 본인 PR에 달린 후속 무응답 코멘트를 보조 신호로 함께 본다.

PR·이슈 번호를 "스레드"의 키로 삼아, 같은 스레드 안의 이벤트들을 시간순으로 늘어놓고
"이 사람이 응답해야 하는데 그 이후 이 사람의 이벤트가 없다"를 판정한다. 활동 수집
직후(github.py의 연동, worker/scheduler.py의 폴링) 호출된다."""

import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.github_event import EventType, RawEvent
from app.models.project import Project, ProjectTeam
from app.models.team import TeamMembership
from app.models.unanswered import UnansweredItem, UnansweredSignal
from app.models.user import User

_THREAD_NUMBER_RE = re.compile(r"/(?:pull|issues)/(\d+)")
_MENTION_RE = re.compile(r"@([A-Za-z0-9_-]+)")


def _thread_key(event: RawEvent) -> str | None:
    match = _THREAD_NUMBER_RE.search(event.url or "")
    return match.group(1) if match else None


def _resolve_target(
    db: Session, project_id: uuid.UUID, handle: str | None, fallback_team_id: uuid.UUID | None
) -> tuple[uuid.UUID | None, uuid.UUID | None]:
    """핸들을 (사용자, 팀)으로 해석한다. 이 프로젝트에 참여 중인 팀 소속이 아니면 특정 개인
    배정을 포기하고 fallback_team_id(보통 PR·이슈 작성자의 팀)로만 대상을 좁힌다."""
    if handle:
        user = db.query(User).filter(User.github_handle == handle).first()
        if user is not None:
            membership = (
                db.query(TeamMembership)
                .join(ProjectTeam, ProjectTeam.team_id == TeamMembership.team_id)
                .filter(ProjectTeam.project_id == project_id, TeamMembership.user_id == user.id)
                .first()
            )
            if membership is not None:
                return user.id, membership.team_id
    return None, fallback_team_id


def _upsert(
    db: Session,
    project_id: uuid.UUID,
    anchor_event: RawEvent,
    signal_type: UnansweredSignal,
    target_user_id: uuid.UUID | None,
    target_team_id: uuid.UUID | None,
    is_resolved: bool,
) -> bool:
    """(raw_event, signal_type, target_user) 조합이 이미 있으면 해결 상태만 갱신하고,
    없으면 새로 만든다. 반환값은 새로 생성했는지 여부."""
    existing = (
        db.query(UnansweredItem)
        .filter(
            UnansweredItem.raw_event_id == anchor_event.id,
            UnansweredItem.signal_type == signal_type,
            UnansweredItem.target_user_id == target_user_id,
        )
        .first()
    )
    if existing is not None:
        # 7.2: 본인이 수동으로 완료 처리한 항목은 자동 재계산이 되돌리지 않는다.
        if not existing.manually_resolved and existing.resolved != is_resolved:
            existing.resolved = is_resolved
            existing.resolved_at = datetime.now(timezone.utc) if is_resolved else None
        return False

    db.add(
        UnansweredItem(
            raw_event_id=anchor_event.id,
            project_id=project_id,
            target_user_id=target_user_id,
            target_team_id=target_team_id,
            signal_type=signal_type,
            resolved=is_resolved,
            resolved_at=datetime.now(timezone.utc) if is_resolved else None,
        )
    )
    # autoflush=False 세션이라, flush 없이 다음 조합을 조회하면 방금 add한 행이 안 보여
    # 같은 실행 안에서 중복 삽입을 시도할 수 있다 (유니크 제약 위반).
    db.flush()
    return True


def detect_unanswered_items(db: Session, project: Project) -> int:
    """프로젝트의 PR·이슈·리뷰코멘트를 스레드별로 묶어 미응답 항목을 찾아낸다.
    반환값은 새로 생성된 항목 수."""
    events = (
        db.query(RawEvent)
        .filter(
            RawEvent.project_id == project.id,
            RawEvent.type.in_([EventType.PR, EventType.ISSUE, EventType.REVIEW_COMMENT]),
        )
        .order_by(RawEvent.gh_created_at.asc())
        .all()
    )

    threads: dict[str, list[RawEvent]] = {}
    roots: dict[str, RawEvent] = {}
    for event in events:
        key = _thread_key(event)
        if key is None:
            continue
        threads.setdefault(key, []).append(event)
        if event.type in (EventType.PR, EventType.ISSUE) and str(event.github_id).endswith(":created"):
            roots[key] = event

    created_count = 0
    for key, thread_events in threads.items():
        root = roots.get(key)
        author_handle = root.actor_handle if root else None
        author_user_id, author_team_id = _resolve_target(db, project.id, author_handle, None)

        # 신호 A: 리뷰어로 지정됐지만 이후 그 리뷰어의 이벤트가 스레드에 없음
        if root is not None:
            for reviewer in (root.raw_payload or {}).get("requested_reviewers", []):
                reviewer_handle = reviewer.get("login")
                if not reviewer_handle:
                    continue
                responded = any(
                    e.actor_handle == reviewer_handle and e.gh_created_at > root.gh_created_at
                    for e in thread_events
                )
                target_user_id, target_team_id = _resolve_target(
                    db, project.id, reviewer_handle, author_team_id
                )
                if _upsert(
                    db, project.id, root, UnansweredSignal.REVIEWER_REQUESTED,
                    target_user_id, target_team_id, is_resolved=responded,
                ):
                    created_count += 1

        # 신호 B: @멘션됐지만 이후 그 사람의 이벤트가 스레드에 없음
        for event in thread_events:
            for mentioned_handle in set(_MENTION_RE.findall(event.body or "")):
                responded = any(
                    e.actor_handle == mentioned_handle and e.gh_created_at > event.gh_created_at
                    for e in thread_events
                )
                target_user_id, target_team_id = _resolve_target(
                    db, project.id, mentioned_handle, author_team_id
                )
                if _upsert(
                    db, project.id, event, UnansweredSignal.MENTIONED,
                    target_user_id, target_team_id, is_resolved=responded,
                ):
                    created_count += 1

        # 신호 C(보조): 본인 PR·이슈에 달린 코멘트인데 본인의 후속 응답이 없음
        if author_handle is not None and root is not None:
            for event in thread_events:
                if event.type != EventType.REVIEW_COMMENT or event.actor_handle == author_handle:
                    continue
                responded = any(
                    e.actor_handle == author_handle and e.gh_created_at > event.gh_created_at
                    for e in thread_events
                )
                if _upsert(
                    db, project.id, event, UnansweredSignal.AUTHOR_REPLY_NEEDED,
                    author_user_id, author_team_id, is_resolved=responded,
                ):
                    created_count += 1

    db.commit()
    return created_count
