import subprocess
from pathlib import Path

import pytest

from app.pipeline.api.schemas import PipelineRequest, RepoFile
from app.repository_source import RepoSyncService


def run_git(repo_path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def create_git_repo(tmp_path: Path) -> Path:
    repo_path = tmp_path / "project"
    repo_path.mkdir()

    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True, text=True)
    run_git(repo_path, "config", "user.email", "test@example.com")
    run_git(repo_path, "config", "user.name", "Test User")

    (repo_path / "app.py").write_text("def run():\n    return True\n", encoding="utf-8")
    (repo_path / "README.md").write_text("# Project\n\nHello repo sync.\n", encoding="utf-8")
    (repo_path / "binary.dat").write_bytes(b"\x00\x01not text")
    (repo_path / "untracked.py").write_text("def ignored(): pass\n", encoding="utf-8")

    run_git(repo_path, "add", "app.py", "README.md", "binary.dat")
    run_git(repo_path, "commit", "-m", "initial commit")

    return repo_path


def create_bare_remote(source_repo_path: Path, tmp_path: Path) -> Path:
    remote_path = tmp_path / "remote.git"
    subprocess.run(
        ["git", "clone", "--bare", str(source_repo_path), str(remote_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return remote_path


def test_sync_builds_snapshot_from_request() -> None:
    service = RepoSyncService()
    request = PipelineRequest(
        repository="team/project",
        branch="main",
        files=[RepoFile(path="app.py", content="def run(): pass\n")],
    )

    snapshot = service.sync(request)

    assert snapshot.repository == "team/project"
    assert snapshot.branch == "main"
    assert snapshot.files == request.files
    assert len(snapshot.commit_sha) == 12


def test_sync_commit_sha_changes_when_file_content_changes() -> None:
    service = RepoSyncService()
    first = service.sync(
        PipelineRequest(files=[RepoFile(path="app.py", content="def run(): pass\n")])
    )
    second = service.sync(
        PipelineRequest(files=[RepoFile(path="app.py", content="def run(): return True\n")])
    )

    assert first.commit_sha != second.commit_sha


def test_sync_rejects_request_without_repository_source() -> None:
    service = RepoSyncService()

    with pytest.raises(ValueError, match="repository_url 또는 files"):
        service.sync(PipelineRequest())


def test_sync_clones_tracked_text_files_from_repository_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_repo_path = create_git_repo(tmp_path)
    remote_path = create_bare_remote(source_repo_path, tmp_path)
    service = RepoSyncService()
    monkeypatch.setenv("REPOPILOT_ALLOW_FILE_REPOSITORY_URL", "1")

    snapshot = service.sync(PipelineRequest(repository_url=remote_path.as_uri()))

    assert snapshot.repository == "remote"
    assert snapshot.branch == run_git(source_repo_path, "rev-parse", "--abbrev-ref", "HEAD")
    assert snapshot.commit_sha == run_git(source_repo_path, "rev-parse", "--short=12", "HEAD")
    assert {file.path for file in snapshot.files} == {"README.md", "app.py"}


def test_sync_rejects_non_github_repository_url() -> None:
    service = RepoSyncService()

    with pytest.raises(ValueError, match=r"repository_url은 https://github\.com/"):
        service.sync(PipelineRequest(repository_url="https://example.com/team/project.git"))


def test_sync_reports_git_command_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout_run(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired(cmd="git status", timeout=30)

    monkeypatch.setattr(subprocess, "run", timeout_run)
    service = RepoSyncService()

    with pytest.raises(ValueError, match="git command timed out"):
        service._run_git(["status"])
