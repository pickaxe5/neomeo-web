import urllib.parse

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.i18n import get_lang, t
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, SignupRequest, TokenPair, UserOut

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
def github_callback(
    code: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """GitHub 인가 코드를 토큰으로 교환하고, 최초 로그인 시 사용자를 자동 생성한다.
    로그인 시점에 GitHub 핸들이 확보되어 별도 매핑 단계가 불필요하다 (A-001).

    이 엔드포인트는 프론트 JS가 아니라 GitHub이 브라우저를 직접 리다이렉트시켜 호출하므로,
    실패 시에도 JSON 에러가 아니라 프론트 로그인 화면으로 되돌려보내야 한다. 사용자가 인가를
    취소하면 GitHub은 code 없이 error=access_denied로 리다이렉트한다."""
    error_redirect = RedirectResponse(f"{settings.frontend_base_url}/login?error=github_auth_failed")
    if error or not code:
        return error_redirect

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
            return error_redirect

        user_resp = client.get(
            GITHUB_USER_API_URL,
            headers={"Authorization": f"Bearer {github_access_token}"},
        )
        gh_user = user_resp.json()
        if "id" not in gh_user:
            return error_redirect

    github_id = str(gh_user["id"])
    github_handle = gh_user["login"]
    github_email = gh_user.get("email")

    user = db.query(User).filter(User.github_id == github_id).first()
    if user is None and github_email:
        # users.email은 unique 제약이 있다. 이메일로 먼저 가입한 계정과 GitHub 이메일이
        # 같으면 새로 INSERT하지 않고(IntegrityError 방지) 기존 계정에 GitHub을 연결한다.
        user = db.query(User).filter(User.email == github_email).first()

    if user is None:
        user = User(
            email=github_email or f"{github_handle}@users.noreply.github.com",
            github_id=github_id,
            github_handle=github_handle,
            name=gh_user.get("name") or github_handle,
            github_access_token=github_access_token,
        )
        db.add(user)
    else:
        user.github_id = github_id
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


@router.post("/signup", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
def signup(
    payload: SignupRequest, db: Session = Depends(get_db), lang: str = Depends(get_lang)
) -> TokenPair:
    """A-002: 이메일 가입. 심사·테스트 계정 전달용이며 가입과 동시에 로그인 처리한다
    (기능명세서 1.2). 이미 가입된 이메일이면 로그인 실패와 동일한 문구로 안내해
    이메일 존재 여부를 노출하지 않는다."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, t("email_taken", lang))

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_token_pair(user)


@router.post("/login", response_model=TokenPair)
def login(
    payload: LoginRequest, db: Session = Depends(get_db), lang: str = Depends(get_lang)
) -> TokenPair:
    """A-002: 자체 로그인. 심사용 테스트 계정은 데모 시드(D-001/D-002)로 발급한다."""
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or user.password_hash is None or not verify_password(
        payload.password, user.password_hash
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, t("invalid_credentials", lang))
    return _issue_token_pair(user)


@router.post("/refresh", response_model=TokenPair)
def refresh(
    payload: RefreshRequest, db: Session = Depends(get_db), lang: str = Depends(get_lang)
) -> TokenPair:
    """A-003: 세션 관리 — 리프레시 토큰으로 액세스 토큰을 갱신한다."""
    user_id = decode_token(payload.refresh_token, expected_type="refresh")
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, t("invalid_refresh_token", lang))
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, t("user_not_found", lang))
    return _issue_token_pair(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> None:
    """A-003: JWT는 상태를 서버에 두지 않으므로, 로그아웃은 클라이언트가 토큰을 폐기하는 것으로 처리한다.
    블랙리스트 인프라는 해커톤 범위(정교하게 만들지 말 것) 밖으로 둔다."""
    return None


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
