import urllib.parse

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_API_URL = "https://api.github.com/user"


def _issue_token_pair(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/github/login")
def github_login() -> RedirectResponse:
    """A-001: GitHub OAuth 로그인 흐름 시작. 프론트는 이 URL로 리다이렉트만 하면 된다."""
    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_oauth_callback_url,
        "scope": "read:user user:email repo",
        "allow_signup": "false",
    }
    return RedirectResponse(f"{GITHUB_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}")


@router.get("/github/callback")
def github_callback(code: str, db: Session = Depends(get_db)) -> RedirectResponse:
    """GitHub 인가 코드를 토큰으로 교환하고, 최초 로그인 시 사용자를 자동 생성한다.
    로그인 시점에 GitHub 핸들이 확보되어 별도 매핑 단계가 불필요하다 (A-001)."""
    with httpx.Client(timeout=10) as client:
        token_resp = client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_oauth_callback_url,
            },
        )
        token_data = token_resp.json()
        github_access_token = token_data.get("access_token")
        if not github_access_token:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "GitHub 인증에 실패했습니다.")

        user_resp = client.get(
            GITHUB_USER_API_URL,
            headers={"Authorization": f"Bearer {github_access_token}"},
        )
        gh_user = user_resp.json()

    github_id = str(gh_user["id"])
    github_handle = gh_user["login"]

    user = db.query(User).filter(User.github_id == github_id).first()
    if user is None:
        user = User(
            email=gh_user.get("email") or f"{github_handle}@users.noreply.github.com",
            github_id=github_id,
            github_handle=github_handle,
            name=gh_user.get("name") or github_handle,
            github_access_token=github_access_token,
        )
        db.add(user)
    else:
        user.github_handle = github_handle
        user.github_access_token = github_access_token

    db.commit()
    db.refresh(user)

    tokens = _issue_token_pair(user)
    redirect_url = (
        f"{settings.frontend_base_url}/oauth/callback"
        f"?access_token={tokens.access_token}&refresh_token={tokens.refresh_token}"
    )
    return RedirectResponse(redirect_url)


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    """A-002: 자체 로그인. 심사용 테스트 계정은 데모 시드(D-001/D-002)로 발급한다."""
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or user.password_hash is None or not verify_password(
        payload.password, user.password_hash
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "이메일 또는 비밀번호가 올바르지 않습니다.")
    return _issue_token_pair(user)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    """A-003: 세션 관리 — 리프레시 토큰으로 액세스 토큰을 갱신한다."""
    user_id = decode_token(payload.refresh_token, expected_type="refresh")
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "유효하지 않거나 만료된 리프레시 토큰입니다.")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "사용자를 찾을 수 없습니다.")
    return _issue_token_pair(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> None:
    """A-003: JWT는 상태를 서버에 두지 않으므로, 로그아웃은 클라이언트가 토큰을 폐기하는 것으로 처리한다.
    블랙리스트 인프라는 해커톤 범위(정교하게 만들지 말 것) 밖으로 둔다."""
    return None


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
