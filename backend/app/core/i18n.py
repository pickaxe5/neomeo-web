"""기능명세서 8.4: API 에러 메시지 다국어 처리. UI 라벨은 프론트가 팀 default_language로
전환하지만, 백엔드가 생성하는 에러 메시지(HTTPException detail)는 지금까지 전부 한국어로
고정되어 있었다. 로그인 여부와 무관하게(401 응답 등) 언어를 판단해야 하므로, 팀 설정을
조회하는 대신 표준 HTTP 방식인 Accept-Language 헤더를 쓴다 — 프론트는 요청 시 이 헤더에
사용자의 팀 언어를 담아 보내면 된다."""

from fastapi import Header

SUPPORTED_LANGS = ("ko", "en")
DEFAULT_LANG = "ko"

MESSAGES: dict[str, dict[str, str]] = {
    "unauthorized": {"ko": "인증이 필요합니다.", "en": "Authentication is required."},
    "invalid_token": {
        "ko": "유효하지 않거나 만료된 토큰입니다.",
        "en": "The token is invalid or has expired.",
    },
    "user_not_found": {"ko": "사용자를 찾을 수 없습니다.", "en": "User not found."},
    "invalid_id": {"ko": "유효하지 않은 ID 형식입니다.", "en": "Invalid ID format."},
    "leader_only": {"ko": "팀장만 수행할 수 있습니다.", "en": "Only the team leader can do this."},
    "project_admin_only": {
        "ko": "프로젝트 관리자만 수행할 수 있습니다.",
        "en": "Only project admins can do this.",
    },
    "project_not_found": {"ko": "프로젝트를 찾을 수 없습니다.", "en": "Project not found."},
    "team_not_found": {"ko": "팀을 찾을 수 없습니다.", "en": "Team not found."},
    "github_auth_failed": {"ko": "GitHub 인증에 실패했습니다.", "en": "GitHub authentication failed."},
    "email_taken": {"ko": "이미 가입된 이메일입니다.", "en": "This email is already registered."},
    "invalid_credentials": {
        "ko": "이메일 또는 비밀번호가 올바르지 않습니다.",
        "en": "Incorrect email or password.",
    },
    "invalid_refresh_token": {
        "ko": "유효하지 않거나 만료된 리프레시 토큰입니다.",
        "en": "The refresh token is invalid or has expired.",
    },
    "github_login_required": {
        "ko": "GitHub 계정으로 먼저 로그인해주세요 (/auth/github/login).",
        "en": "Please log in with GitHub first (/auth/github/login).",
    },
    "briefing_item_not_found": {
        "ko": "브리핑 항목을 찾을 수 없습니다.",
        "en": "Briefing item not found.",
    },
    "briefing_item_forbidden": {
        "ko": "본인의 브리핑 항목만 처리할 수 있습니다.",
        "en": "You can only process your own briefing items.",
    },
    "demo_account_missing": {
        "ko": "데모 계정이 없습니다. 먼저 /demo/seed를 호출하세요.",
        "en": "Demo account not found. Call /demo/seed first.",
    },
    "not_team_member": {"ko": "이 팀의 멤버가 아닙니다.", "en": "You are not a member of this team."},
    "last_leader_cannot_leave": {
        "ko": "마지막 팀장은 팀을 나갈 수 없습니다. 팀을 삭제하거나 다른 팀원이 먼저 팀장이 되어야 합니다.",
        "en": "The last team leader cannot leave. Delete the team or have another member "
        "become leader first.",
    },
    "last_leader_cannot_be_demoted": {
        "ko": "마지막 팀장은 강등할 수 없습니다. 다른 팀원을 먼저 팀장으로 위임해주세요.",
        "en": "The last team leader cannot be demoted. Assign another member as leader first.",
    },
    "cannot_remove_self": {
        "ko": "본인을 팀에서 내보낼 수 없습니다. 팀을 나가려면 나가기 기능을 사용해주세요.",
        "en": "You cannot remove yourself from the team. Use the leave-team action instead.",
    },
    "repo_not_connected": {
        "ko": "이 프로젝트에 연결된 레포가 아닙니다.",
        "en": "This repo is not connected to the project.",
    },
    "document_file_too_large": {
        "ko": "파일 크기가 너무 큽니다. 최대 {max_mb}MB까지 업로드할 수 있습니다.",
        "en": "The file is too large. Maximum upload size is {max_mb}MB.",
    },
    "team_members_only": {
        "ko": "팀 멤버만 조회할 수 있습니다.",
        "en": "Only team members can view this.",
    },
    "invite_link_invalid": {"ko": "유효하지 않은 초대 링크입니다.", "en": "This invite link is invalid."},
    "invite_link_expired": {"ko": "만료된 초대 링크입니다.", "en": "This invite link has expired."},
    "language_card_not_found": {
        "ko": "'{language}' 언어 카드가 없습니다.",
        "en": "No summary card found for language '{language}'.",
    },
}


def parse_lang(accept_language: str | None) -> str:
    if not accept_language:
        return DEFAULT_LANG
    primary = accept_language.split(",")[0].split("-")[0].strip().lower()
    return primary if primary in SUPPORTED_LANGS else DEFAULT_LANG


def get_lang(accept_language: str | None = Header(default=None)) -> str:
    """프론트는 요청 시 `Accept-Language: en` 또는 `Accept-Language: ko`를 보내면 된다.
    표준 HTTP 헤더라 401처럼 인증 전에 발생하는 에러에도 그대로 쓸 수 있다."""
    return parse_lang(accept_language)


def t(key: str, lang: str, **kwargs) -> str:
    catalog = MESSAGES.get(key)
    if catalog is None:
        return key
    template = catalog.get(lang, catalog[DEFAULT_LANG])
    return template.format(**kwargs) if kwargs else template
