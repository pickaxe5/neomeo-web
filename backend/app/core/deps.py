import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.i18n import get_lang, t
from app.core.security import decode_token
from app.models.project import ProjectAdmin
from app.models.team import TeamMembership, TeamRole
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    lang: str = Depends(get_lang),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, t("unauthorized", lang))

    user_id = decode_token(credentials.credentials, expected_type="access")
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, t("invalid_token", lang))

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, t("user_not_found", lang))
    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """get_current_user와 달리 토큰이 없거나 유효하지 않아도 401 대신 None을 반환한다.
    비로그인 조회도 허용하는 엔드포인트에서 로그인 시에만 추가 정보(예: is_admin)를 채울 때 사용."""
    if credentials is None:
        return None
    user_id = decode_token(credentials.credentials, expected_type="access")
    if user_id is None:
        return None
    return db.get(User, user_id)


def uuid_or_400(value: str, lang: str = "ko") -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, t("invalid_id", lang))


def require_team_leader(db: Session, team_id, user: User, lang: str = "ko") -> None:
    """팀장 전용 작업(팀 설정, 초대 링크 발급, 추가 작업 마감) 권한 확인."""
    membership = (
        db.query(TeamMembership)
        .filter(TeamMembership.team_id == team_id, TeamMembership.user_id == user.id)
        .first()
    )
    if membership is None or membership.role != TeamRole.LEADER:
        raise HTTPException(status.HTTP_403_FORBIDDEN, t("leader_only", lang))


def require_project_admin(db: Session, project_id, user: User, lang: str = "ko") -> None:
    """프로젝트 관리자 전용 작업(설정 수정, 레포 연동, 참여 팀 추가, 초대 링크 발급, 삭제) 권한 확인."""
    admin = (
        db.query(ProjectAdmin)
        .filter(ProjectAdmin.project_id == project_id, ProjectAdmin.user_id == user.id)
        .first()
    )
    if admin is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, t("project_admin_only", lang))
