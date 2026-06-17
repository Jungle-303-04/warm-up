import os
import subprocess
from hashlib import sha1
from pathlib import Path
from urllib.parse import unquote, urlparse

from app.pipeline.router import (
    DEFAULT_BRANCH,
    DEFAULT_REPO,
    PipelineRequest,
    RepoFile,
    RepoSnapshot,
)
from app.repository_source.fetcher import GitSubprocessFetcher, RepositoryFetcher
from app.validation import required_text

MAX_BYTES = 200_000
ALLOW_FILE_URL = "REPOLM_ALLOW_FILE_REPOSITORY_URL"
GIT_TIMEOUT = 30


class RepoSyncService:
    def __init__(self, fetcher: RepositoryFetcher | None = None) -> None:
        self._fetcher = fetcher or GitSubprocessFetcher()

    def sync(self, request: PipelineRequest) -> RepoSnapshot:
        if request.repository_url is not None:
            return self._sync_remote_repository(request)

        return self._sync_request_files(request)

    def _sync_request_files(self, request: PipelineRequest) -> RepoSnapshot:
        if not request.files:
            raise ValueError("repository_url 또는 files가 필요합니다")

        digest = sha1()
        digest.update(request.repository.encode())
        digest.update(request.branch.encode())

        for file in request.files:
            digest.update(file.path.encode())
            digest.update(file.content.encode())

        return RepoSnapshot(
            repository=request.repository,
            branch=request.branch,
            commit_sha=digest.hexdigest()[:12],
            files=request.files,
        )

    def _sync_remote_repository(self, request: PipelineRequest) -> RepoSnapshot:
        repository_url = required_text(
            request.repository_url or "",
            "repository_url은 비어 있을 수 없습니다",
        )
        self._validate_repository_url(repository_url)

        branch = None if request.branch == DEFAULT_BRANCH else request.branch

        import hashlib
        url_hash = hashlib.sha256(repository_url.encode("utf-8")).hexdigest()[:16]
        # data/git_cache 디렉토리를 사용해 영구 보존 캐시 구성
        cache_base = Path("data/git_cache")
        clone_path = cache_base / url_hash

        self._fetcher.fetch(repository_url, branch, clone_path)
        return self._snapshot_from_local_repository(
            clone_path,
            request.repository,
            repository_url,
        )

    def _snapshot_from_local_repository(
        self,
        repo_path: Path,
        requested_repository: str,
        repository_url: str | None = None,
    ) -> RepoSnapshot:
        root = Path(self._git(repo_path, "rev-parse", "--show-toplevel")).resolve()
        branch = self._git(root, "rev-parse", "--abbrev-ref", "HEAD")
        commit_sha = self._git(root, "rev-parse", "--short=12", "HEAD")
        repository = self._repository_name(requested_repository, root, repository_url)

        return RepoSnapshot(
            repository=repository,
            branch=branch,
            commit_sha=commit_sha,
            files=self._read_tracked_text_files(root),
        )

    def _read_tracked_text_files(self, root: Path) -> list[RepoFile]:
        files: list[RepoFile] = []

        for relative_path in self._git(root, "ls-files", "-z").split("\0"):
            if not relative_path:
                continue

            path = root / relative_path
            if not path.is_file():
                continue

            content = self._read_text_file(path)
            if content is None:
                continue

            files.append(RepoFile(path=relative_path, content=content))

        return files

    def _read_text_file(self, path: Path) -> str | None:
        try:
            data = path.read_bytes()
        except OSError:
            return None

        if len(data) > MAX_BYTES or b"\0" in data:
            return None

        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return None

    def _repository_name(
        self,
        requested_repository: str,
        root: Path,
        repository_url: str | None = None,
    ) -> str:
        if requested_repository != DEFAULT_REPO:
            return requested_repository

        if repository_url:
            return self._repository_name_from_remote(repository_url)

        remote = self._git_or_none(root, "config", "--get", "remote.origin.url")
        if remote:
            return self._repository_name_from_remote(remote)

        return root.name

    def _repository_name_from_remote(self, remote: str) -> str:
        raw_value = remote.strip()
        parsed = urlparse(raw_value)
        if parsed.scheme == "file":
            path = unquote(parsed.path).removesuffix(".git")
            return Path(path).name or "local-repository"

        value = raw_value.removesuffix(".git")
        if ":" in value and not value.startswith(("http://", "https://")):
            value = value.split(":", 1)[1]
        elif value.startswith(("/", ".")):
            return Path(value).name or "local-repository"

        parts = [part for part in value.replace("\\", "/").split("/") if part]
        if len(parts) >= 2:
            return "/".join(parts[-2:])
        if parts:
            return parts[-1]
        return "local-repository"

    def _clone_repository(self, repository_url: str, branch: str | None, clone_path: Path) -> None:
        command = ["clone", "--depth", "1"]
        if branch:
            command.extend(["--branch", branch])
        command.extend([repository_url, str(clone_path)])
        self._run_git(command)

    def _validate_repository_url(self, repository_url: str) -> None:
        parsed = urlparse(repository_url)
        if parsed.scheme == "https" and parsed.netloc == "github.com" and parsed.path.strip("/"):
            return

        allow_file_url = os.environ.get(ALLOW_FILE_URL) == "1"
        if parsed.scheme == "file" and allow_file_url:
            return

        raise ValueError(
            "repository_url은 https://github.com/... URL이어야 합니다"
            f" 또는 {ALLOW_FILE_URL}=1일 때 file:// URL이어야 합니다"
        )

    def _git(self, repo_path: Path, *args: str) -> str:
        return self._run_git(["-C", str(repo_path), *args])

    def _run_git(self, args: list[str]) -> str:
        try:
            result = subprocess.run(
                ["git", *args],
                check=True,
                capture_output=True,
                text=True,
                timeout=GIT_TIMEOUT,
            )
        except FileNotFoundError as exc:
            raise ValueError("git executable was not found") from exc
        except subprocess.TimeoutExpired as exc:
            raise ValueError(
                f"git command timed out after {GIT_TIMEOUT} seconds"
            ) from exc
        except subprocess.CalledProcessError as exc:
            detail = exc.stderr.strip() or exc.stdout.strip() or "git command failed"
            raise ValueError(f"git repository sync failed: {detail}") from exc

        return result.stdout.strip()

    def _git_or_none(self, repo_path: Path, *args: str) -> str | None:
        try:
            return self._git(repo_path, *args)
        except ValueError:
            return None
