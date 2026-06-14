from urllib.parse import quote

import httpx

from app.domains.github.api.schema import GitHubFileResponseDTO
from app.domains.rag.api.schema import (
    GitHubRagPipelineRequestDTO,
    GitHubRepositoryIndexRequestDTO,
)


GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_API_ACCEPT_HEADER = "application/vnd.github+json"
GITHUB_API_VERSION = "2022-11-28"
USER_AGENT = "warm-up-code-trust-kanban"
REQUEST_TIMEOUT_SECONDS = 15
SUPPORTED_RAG_EXTENSIONS = (".py", ".md")
MAX_GITHUB_FILE_SIZE_BYTES = 120_000
IGNORED_PATH_PARTS = {
    ".git",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}


class GitHubRepositoryClient:
    def build_pipeline_request_from_repository(
        self,
        access_token: str,
        request: GitHubRepositoryIndexRequestDTO,
    ) -> GitHubRagPipelineRequestDTO:
        repository = self.fetch_repository(access_token, request.repository_full_name)
        branch = request.branch or repository["default_branch"]
        commit_sha = self.fetch_branch_commit_sha(
            access_token=access_token,
            repository_full_name=request.repository_full_name,
            branch=branch,
        )
        tree_items = self.fetch_repository_tree(
            access_token=access_token,
            repository_full_name=request.repository_full_name,
            commit_sha=commit_sha,
        )
        files = self.fetch_supported_files(
            access_token=access_token,
            repository_full_name=request.repository_full_name,
            commit_sha=commit_sha,
            tree_items=tree_items,
        )

        if not files:
            raise ValueError("no Python or Markdown files were found for indexing")

        return GitHubRagPipelineRequestDTO(
            repository_full_name=request.repository_full_name,
            branch=branch,
            commit_sha=commit_sha,
            files=files,
        )

    def fetch_repository(self, access_token: str, repository_full_name: str) -> dict:
        return self.get_json(
            access_token,
            f"/repos/{quote_repository_full_name(repository_full_name)}",
        )

    def fetch_branch_commit_sha(
        self,
        access_token: str,
        repository_full_name: str,
        branch: str,
    ) -> str:
        payload = self.get_json(
            access_token,
            (
                f"/repos/{quote_repository_full_name(repository_full_name)}"
                f"/branches/{quote_value(branch)}"
            ),
        )
        commit_sha = payload.get("commit", {}).get("sha")
        if not isinstance(commit_sha, str) or not commit_sha.strip():
            raise ValueError("github branch response does not contain commit sha")
        return commit_sha

    def fetch_repository_tree(
        self,
        access_token: str,
        repository_full_name: str,
        commit_sha: str,
    ) -> list[dict]:
        payload = self.get_json(
            access_token,
            (
                f"/repos/{quote_repository_full_name(repository_full_name)}"
                f"/git/trees/{quote_value(commit_sha)}?recursive=1"
            ),
        )
        tree = payload.get("tree")
        if not isinstance(tree, list):
            raise ValueError("github tree response is invalid")
        return tree

    def fetch_supported_files(
        self,
        access_token: str,
        repository_full_name: str,
        commit_sha: str,
        tree_items: list[dict],
    ) -> list[GitHubFileResponseDTO]:
        files: list[GitHubFileResponseDTO] = []
        for item in tree_items:
            path = item.get("path")
            if not self.is_supported_blob(item, path):
                continue

            files.append(
                self.fetch_file_content(
                    access_token=access_token,
                    repository_full_name=repository_full_name,
                    path=path,
                    ref=commit_sha,
                )
            )

        return files

    def fetch_file_content(
        self,
        access_token: str,
        repository_full_name: str,
        path: str,
        ref: str,
    ) -> GitHubFileResponseDTO:
        payload = self.get_json(
            access_token,
            (
                f"/repos/{quote_repository_full_name(repository_full_name)}"
                f"/contents/{quote_file_path(path)}?ref={quote_value(ref)}"
            ),
        )
        return GitHubFileResponseDTO.model_validate(payload)

    def get_json(self, access_token: str, path: str) -> dict:
        response = httpx.get(
            f"{GITHUB_API_BASE_URL}{path}",
            headers=self.build_headers(access_token),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError("github api response is not valid json") from exc

        if response.status_code >= 400:
            message = payload.get("message") if isinstance(payload, dict) else None
            raise ValueError(message or "github api request failed")

        if not isinstance(payload, dict):
            raise ValueError("github api response is invalid")

        return payload

    def build_headers(self, access_token: str) -> dict[str, str]:
        return {
            "Accept": GITHUB_API_ACCEPT_HEADER,
            "Authorization": f"Bearer {access_token}",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }

    def is_supported_blob(self, item: dict, path: str | None) -> bool:
        if item.get("type") != "blob" or not path:
            return False

        if item.get("size", 0) > MAX_GITHUB_FILE_SIZE_BYTES:
            return False

        normalized_parts = {part.lower() for part in path.split("/")}
        if normalized_parts & IGNORED_PATH_PARTS:
            return False

        return path.lower().endswith(SUPPORTED_RAG_EXTENSIONS)


def quote_repository_full_name(repository_full_name: str) -> str:
    owner, repo = repository_full_name.split("/", 1)
    return f"{quote_value(owner)}/{quote_value(repo)}"


def quote_value(value: str) -> str:
    return quote(value, safe="")


def quote_file_path(value: str) -> str:
    return quote(value, safe="/")
