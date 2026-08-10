import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.team import TeamMembership, TeamRole
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "인증이 필요합니다.")

    user_id = decode_token(credentials.credentials, expected_type="access")
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "유효하지 않거나 만료된 토큰입니다.")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "사용자를 찾을 수 없습니다.")
    return user


def uuid_or_400(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "유효하지 않은 ID 형식입니다.")


def require_team_leader(db: Session, team_id, user: User) -> None:
    """팀장 전용 작업(팀 설정, 초대 링크 발급, 추가 작업 마감) 권한 확인."""
    membership = (
        db.query(TeamMembership)
        .filter(TeamMembership.team_id == team_id, TeamMembership.user_id == user.id)
        .first()
    )
    if membership is None or membership.role != TeamRole.LEADER:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "팀장만 수행할 수 있습니다.")
