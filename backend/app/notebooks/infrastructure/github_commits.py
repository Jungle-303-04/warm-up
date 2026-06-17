"""GitHub commit metadata fetcher for notebook repo sources."""

from dataclasses import dataclass
from urllib.parse import quote, urlparse

import httpx

from app.auth.domain.ports import GitHubTokenStore
from app.notebooks.domain.records import SourceRecord

REQUEST_TIMEOUT_SECONDS = 10.0
MAX_COMMITS = 5


@dataclass(slots=True)
class GitHubCommitFetcher:
    token_store: GitHubTokenStore

    def __call__(self, source: SourceRecord, owner_user_id: int) -> list[dict]:
        parsed = _parse_github_repo(source.repository_url)
        if parsed is None:
            return []
        owner, repo = parsed
        token = self.token_store.get(owner_user_id)
        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        params = {"per_page": str(MAX_COMMITS)}
        if source.branch:
            params["sha"] = source.branch
        url = (
            "https://api.github.com/repos/"
            f"{quote(owner, safe='')}/{quote(repo, safe='')}/commits"
        )
        try:
            response = httpx.get(
                url,
                headers=headers,
                params=params,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return []

        payload = response.json()
        if not isinstance(payload, list):
            return []
        commits: list[dict] = []
        for item in payload[:MAX_COMMITS]:
            if not isinstance(item, dict):
                continue
            raw_commit = item.get("commit")
            commit = raw_commit if isinstance(raw_commit, dict) else {}
            raw_author = commit.get("author")
            author = raw_author if isinstance(raw_author, dict) else {}
            sha = str(item.get("sha") or "")
            if not sha:
                continue
            commits.append(
                {
                    "sha": sha,
                    "short_sha": sha[:12],
                    "message": str(commit.get("message") or "").splitlines()[0],
                    "author_name": author.get("name"),
                    "author_email": author.get("email"),
                    "authored_at": author.get("date"),
                    "html_url": item.get("html_url"),
                    "files": _commit_files(item.get("url"), headers),
                }
            )
        return commits


def _parse_github_repo(url: str | None) -> tuple[str, str] | None:
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        return None
    return parts[0], parts[1].removesuffix(".git")


def _commit_files(url: object, headers: dict[str, str]) -> list[dict[str, str]]:
    if not isinstance(url, str) or not url:
        return []
    try:
        response = httpx.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except httpx.HTTPError:
        return []
    payload = response.json()
    if not isinstance(payload, dict):
        return []
    files = payload.get("files")
    if not isinstance(files, list):
        return []
    out: list[dict[str, str]] = []
    for item in files[:20]:
        if not isinstance(item, dict):
            continue
        filename = item.get("filename")
        if not isinstance(filename, str) or not filename:
            continue
        status = item.get("status")
        out.append(
            {
                "path": filename,
                "status": str(status or "modified"),
            }
        )
    return out
