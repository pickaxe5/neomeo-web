"""httpx 기반 얇은 GitHub REST API 래퍼. 정규화·팀귀속 로직은 github_collector.py가 담당하고,
여기서는 응답 JSON을 그대로 반환한다 (테스트에서 모킹하기 쉽도록 얇게 유지)."""

from datetime import datetime

import httpx

GITHUB_API_BASE = "https://api.github.com"


class GithubApiError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(message)


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get(client: httpx.Client, token: str, path: str, params: dict | None = None) -> httpx.Response:
    resp = client.get(f"{GITHUB_API_BASE}{path}", headers=_headers(token), params=params)
    if resp.status_code >= 400:
        raise GithubApiError(resp.status_code, f"GitHub API 오류 ({resp.status_code}): {path}")
    return resp


def get_repo(client: httpx.Client, token: str, full_name: str) -> dict:
    """G-001: 레포 접근 권한 검증. 404/403이면 접근 불가로 GithubApiError가 발생한다."""
    return _get(client, token, f"/repos/{full_name}").json()


def list_user_repos(client: httpx.Client, token: str) -> list[dict]:
    """docs/frontend-to-backend-requests.md #1: 사용자 본인 + 소속 organization의 레포 전체 목록.
    페이지네이션 끝까지 순회한다 (최대 100개/페이지)."""
    results: list[dict] = []
    page = 1
    while True:
        items = _get(
            client,
            token,
            "/user/repos",
            {"affiliation": "owner,organization_member", "per_page": 100, "page": page},
        ).json()
        if not items:
            break
        results.extend(items)
        if len(items) < 100:
            break
        page += 1
    return results


def _paginate_until_before(
    client: httpx.Client, token: str, path: str, params: dict, since: datetime, updated_at_key: str = "updated_at"
) -> list[dict]:
    """updated(수정) 시각 내림차순 정렬 목록에서 since 이후 항목만 모아 반환한다.
    한 페이지가 전부 since 이전이면 더 뒤 페이지는 볼 필요가 없어 조회를 멈춘다."""
    results: list[dict] = []
    page = 1
    while True:
        items = _get(client, token, path, {**params, "page": page, "per_page": 50}).json()
        if not items:
            break
        stop = False
        for item in items:
            updated_at = datetime.fromisoformat(item[updated_at_key].replace("Z", "+00:00"))
            if updated_at < since:
                stop = True
                break
            results.append(item)
        if stop or len(items) < 50:
            break
        page += 1
    return results


def list_pull_requests(client: httpx.Client, token: str, full_name: str, since: datetime) -> list[dict]:
    """G-003: PR(생성·머지). state=all + updated 내림차순 정렬로 since 이후 변경분만 가져온다."""
    return _paginate_until_before(
        client, token, f"/repos/{full_name}/pulls", {"state": "all", "sort": "updated", "direction": "desc"}, since
    )


def list_issues(client: httpx.Client, token: str, full_name: str, since: datetime) -> list[dict]:
    """G-003: 이슈(생성·종료). GitHub issues 엔드포인트는 PR도 함께 반환하므로
    "pull_request" 키가 있는 항목은 호출부에서 걸러내야 한다."""
    items = _get(
        client,
        token,
        f"/repos/{full_name}/issues",
        {"state": "all", "since": since.isoformat(), "sort": "updated", "direction": "desc", "per_page": 100},
    ).json()
    return [item for item in items if "pull_request" not in item]


def list_review_comments(client: httpx.Client, token: str, full_name: str, since: datetime) -> list[dict]:
    """G-003: PR 리뷰 코멘트. `since` 파라미터를 API가 직접 지원한다."""
    return _get(
        client,
        token,
        f"/repos/{full_name}/pulls/comments",
        {"since": since.isoformat(), "sort": "created", "direction": "asc", "per_page": 100},
    ).json()


def list_commits(client: httpx.Client, token: str, full_name: str, since: datetime, limit: int = 20) -> list[dict]:
    """G-005: 커밋은 노이즈가 커서 근거자료·담당 추론에만 쓰인다. API 사용량 절제를 위해
    최근 N개로 캡한다."""
    return _get(
        client,
        token,
        f"/repos/{full_name}/commits",
        {"since": since.isoformat(), "per_page": limit},
    ).json()


def get_commit_files(client: httpx.Client, token: str, full_name: str, sha: str) -> list[str]:
    """G-005: 커밋 1건의 변경 파일 경로 목록 (담당 영역 추론용)."""
    data = _get(client, token, f"/repos/{full_name}/commits/{sha}").json()
    return [f["filename"] for f in data.get("files", [])]
