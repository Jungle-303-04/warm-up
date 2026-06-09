from app.schemas.pipeline import PipelineRequest, RepoFile
from app.services.repo_sync import RepoSyncService


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
