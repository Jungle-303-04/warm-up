from urllib.parse import quote

from app.external.http import HttpClientPort, HttpRequest, HttpRequestError
from app.github.api.schema import GitHubFileResponseDTO
from app.rag.api.schema import (
    GitHubRagPipelineRequestDTO,
    GitHubRepositoryIndexRequestDTO,
    GitHubRepositoryRefDTO,
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
    """GitHub API에서 레포 메타데이터, tree, 파일 내용을 가져와 RAG 입력으로 만든다."""

    def __init__(self, http_client: HttpClientPort) -> None:
        self.http_client = http_client

    def build_pipeline_request_from_repository(
        self,
        access_token: str,
        request: GitHubRepositoryIndexRequestDTO,
    ) -> GitHubRagPipelineRequestDTO:
        """owner/repo 요청 하나로 기본 branch, commit, 지원 파일 목록을 모두 수집한다."""

        repository_ref = self.resolve_repository_ref(access_token, request)
        return self.build_pipeline_request_from_ref(access_token, repository_ref)

    def resolve_repository_ref(
        self,
        access_token: str,
        request: GitHubRepositoryIndexRequestDTO,
    ) -> GitHubRepositoryRefDTO:
        """파일 수집 전에 레포, 브랜치, 현재 commit 기준만 먼저 확정한다."""

        repository = self.fetch_repository(access_token, request.repository_full_name)
        branch = request.branch or repository["default_branch"]
        commit_sha = self.fetch_branch_commit_sha(
            access_token=access_token,
            repository_full_name=request.repository_full_name,
            branch=branch,
        )

        return GitHubRepositoryRefDTO(
            repository_full_name=request.repository_full_name,
            branch=branch,
            commit_sha=commit_sha,
        )

    def build_pipeline_request_from_ref(
        self,
        access_token: str,
        repository_ref: GitHubRepositoryRefDTO,
    ) -> GitHubRagPipelineRequestDTO:
        """이미 확정한 commit 기준으로 tree와 파일 본문만 수집한다."""

        tree_items = self.fetch_repository_tree(
            access_token=access_token,
            repository_full_name=repository_ref.repository_full_name,
            commit_sha=repository_ref.commit_sha,
        )
        files = self.fetch_supported_files(
            access_token=access_token,
            repository_full_name=repository_ref.repository_full_name,
            commit_sha=repository_ref.commit_sha,
            tree_items=tree_items,
        )

        if not files:
            raise ValueError("no Python or Markdown files were found for indexing")

        return GitHubRagPipelineRequestDTO(
            repository_full_name=repository_ref.repository_full_name,
            branch=repository_ref.branch,
            commit_sha=repository_ref.commit_sha,
            files=files,
        )

    def fetch_repository(self, access_token: str, repository_full_name: str) -> dict:
        """기본 branch 같은 레포지토리 메타데이터를 가져온다."""

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
        """분석 기준을 고정하기 위해 branch가 가리키는 commit sha를 조회한다."""

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
        """레포 전체 파일 경로를 훑기 위해 recursive git tree를 가져온다."""

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
        """tree에서 Python/Markdown 파일만 골라 Contents API 응답으로 변환한다."""

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
        """특정 commit 기준의 파일 본문을 가져와 DTO 검증까지 수행한다."""

        payload = self.get_json(
            access_token,
            (
                f"/repos/{quote_repository_full_name(repository_full_name)}"
                f"/contents/{quote_file_path(path)}?ref={quote_value(ref)}"
            ),
        )
        return GitHubFileResponseDTO.model_validate(payload)

    def get_json(self, access_token: str, path: str) -> dict:
        """GitHub API 호출 오류를 서비스 레이어가 처리하기 쉬운 ValueError로 바꾼다."""

        try:
            payload = self.http_client.request_json(
                HttpRequest(
                    method="GET",
                    url=f"{GITHUB_API_BASE_URL}{path}",
                    headers=self.build_headers(access_token),
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
            )
        except HttpRequestError as exc:
            raise ValueError(str(exc)) from exc

        if not isinstance(payload, dict):
            raise ValueError("github api response is invalid")

        return payload

    def build_headers(self, access_token: str) -> dict[str, str]:
        """GitHub REST API 호출에 필요한 인증과 버전 헤더를 한 곳에서 만든다."""

        return {
            "Accept": GITHUB_API_ACCEPT_HEADER,
            "Authorization": f"Bearer {access_token}",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }

    def is_supported_blob(self, item: dict, path: str | None) -> bool:
        """용량, 폴더, 확장자 기준으로 RAG MVP가 처리할 파일만 통과시킨다."""

        if item.get("type") != "blob" or not path:
            return False

        if item.get("size", 0) > MAX_GITHUB_FILE_SIZE_BYTES:
            return False

        normalized_parts = {part.lower() for part in path.split("/")}
        if normalized_parts & IGNORED_PATH_PARTS:
            return False

        return path.lower().endswith(SUPPORTED_RAG_EXTENSIONS)


def quote_repository_full_name(repository_full_name: str) -> str:
    """owner/repo의 각 구간을 URL path에 안전하게 넣을 수 있게 인코딩한다."""

    owner, repo = repository_full_name.split("/", 1)
    return f"{quote_value(owner)}/{quote_value(repo)}"


def quote_value(value: str) -> str:
    """branch, owner, repo 값을 URL path segment로 안전하게 인코딩한다."""

    return quote(value, safe="")


def quote_file_path(value: str) -> str:
    """파일 경로의 슬래시는 유지하고 각 path segment의 특수문자만 인코딩한다."""

    return quote(value, safe="/")
