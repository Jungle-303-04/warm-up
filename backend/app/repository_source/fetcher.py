import os
import subprocess
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

GIT_TIMEOUT = 30


class RepositoryFetcher(Protocol):
    """원격 저장소를 로컬 캐시 디렉토리로 동기화하는 페처 포트."""

    def fetch(self, repository_url: str, branch: str | None, dest_path: Path) -> Path:
        """저장소를 dest_path로 clone/fetch하고 해당 로컬 경로를 반환합니다."""
        ...


class GitSubprocessFetcher:
    """Git 하위 프로세스를 실행하여 로컬 캐시를 이용해 저장소를 가져오는 구현체."""

    def __init__(self, timeout: int = GIT_TIMEOUT) -> None:
        self._timeout = timeout

    def fetch(self, repository_url: str, branch: str | None, dest_path: Path) -> Path:
        dest_path.mkdir(parents=True, exist_ok=True)
        git_dir = dest_path / ".git"

        if git_dir.exists():
            # 캐시가 이미 존재하므로 fetch 후 checkout 수행
            try:
                # 1) remote url 일치 여부 체크
                current_remote = self._run_git(["-C", str(dest_path), "config", "--get", "remote.origin.url"])
                if current_remote.strip() == repository_url.strip():
                    self._run_git(["-C", str(dest_path), "fetch", "origin", "--depth=1", "--prune"])
                    target_branch = branch or "main"
                    self._run_git(["-C", str(dest_path), "checkout", "-B", target_branch, f"origin/{target_branch}"])
                    self._run_git(["-C", str(dest_path), "reset", "--hard", f"origin/{target_branch}"])
                    return dest_path
            except Exception:
                # 캐시 복구가 안 될 경우 폴더를 다 지우고 새로 clone
                self._clear_directory(dest_path)

        # 캐시가 없거나 복구 실패 시 clone 수행
        command = ["clone", "--depth", "1"]
        if branch:
            command.extend(["--branch", branch])
        command.extend([repository_url, str(dest_path)])
        self._run_git(command)
        return dest_path

    def _clear_directory(self, path: Path) -> None:
        import shutil
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)

    def _run_git(self, args: list[str]) -> str:
        try:
            result = subprocess.run(
                ["git", *args],
                check=True,
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
            return result.stdout.strip()
        except FileNotFoundError as exc:
            raise ValueError("git executable was not found") from exc
        except subprocess.TimeoutExpired as exc:
            raise ValueError(
                f"git command timed out after {self._timeout} seconds"
            ) from exc
        except subprocess.CalledProcessError as exc:
            detail = exc.stderr.strip() or exc.stdout.strip() or "git command failed"
            raise ValueError(f"git operation failed: {detail}") from exc
