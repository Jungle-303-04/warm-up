from datetime import UTC, datetime

from app.schemas.pipeline import PipelineRequest, RepoFile
from app.schemas.repo_rag import RepoRagSyncRequest
from app.services.repo_rag_sync import RepoRagSyncService


def sync_request(repository: str, files: list[RepoFile]) -> RepoRagSyncRequest:
    return RepoRagSyncRequest(repository=repository, branch="main", files=files)


def test_manual_sync_persists_job_snapshot_files_chunks_and_events() -> None:
    service = RepoRagSyncService()

    response = service.run(
        sync_request(
            "team/repo",
            [
                RepoFile(path="README.md", content="# Repo\n\nHello RAG.\n"),
                RepoFile(path="app.py", content="def run():\n    return True\n"),
            ],
        )
    )

    assert response.job.status == "succeeded"
    assert response.job.trigger_type == "manual"
    assert response.repository.repository == "team/repo"
    assert {change.path: change.status for change in response.changes} == {
        "README.md": "added",
        "app.py": "added",
    }
    assert {chunk.source_path for chunk in response.active_chunks} == {"README.md", "app.py"}
    assert [event.stage for event in response.events] == [
        "job_queued",
        "job_started",
        "lock_acquired",
        "fetch_started",
        "fetch_completed",
        "diff_completed",
        "files_persisted",
        "chunks_upserted",
        "job_succeeded",
    ]
    assert len(service.store.snapshots) == 1
    assert len(service.store.files) == 2
    assert len(service.store.chunks) == 2


def test_second_sync_detects_diff_and_soft_deletes_inactive_chunks() -> None:
    service = RepoRagSyncService()

    service.run(
        sync_request(
            "team/repo",
            [
                RepoFile(path="app.py", content="def run():\n    return False\n"),
                RepoFile(path="docs.md", content="# Old docs\n"),
                RepoFile(path="same.py", content="VALUE = 1\n"),
            ],
        )
    )
    response = service.run(
        sync_request(
            "team/repo",
            [
                RepoFile(path="app.py", content="def run():\n    return True\n"),
                RepoFile(path="new.py", content="def created():\n    return True\n"),
                RepoFile(path="same.py", content="VALUE = 1\n"),
            ],
        )
    )

    assert {change.path: change.status for change in response.changes} == {
        "app.py": "modified",
        "docs.md": "deleted",
        "new.py": "added",
        "same.py": "unchanged",
    }
    assert {chunk.source_path for chunk in response.active_chunks} == {
        "app.py",
        "new.py",
        "same.py",
    }
    assert all(chunk.source_path != "docs.md" for chunk in response.active_chunks)

    inactive_chunks = [chunk for chunk in service.store.chunks.values() if not chunk.is_active]
    assert {chunk.source_path for chunk in inactive_chunks} == {"app.py", "docs.md"}
    assert all(chunk.deleted_at is not None for chunk in inactive_chunks)


def test_producers_dedupe_active_jobs_for_same_repository_branch() -> None:
    service = RepoRagSyncService()
    request = PipelineRequest(
        repository="team/repo",
        files=[RepoFile(path="app.py", content="def run(): pass\n")],
    )
    webhook_request = PipelineRequest(
        repository="team/webhook-repo",
        files=[RepoFile(path="app.py", content="def run(): pass\n")],
    )

    manual_job = service.producer.enqueue_manual(request)
    schedule_job = service.producer.enqueue_schedule(request)
    webhook_job = service.producer.enqueue_webhook(
        webhook_request,
        requested_commit_sha="abc123",
    )
    duplicate_webhook_job = service.producer.enqueue_webhook(
        webhook_request,
        requested_commit_sha="abc123",
    )

    assert manual_job.id == schedule_job.id
    assert webhook_job.id == duplicate_webhook_job.id
    assert {manual_job.id, webhook_job.id} <= set(service.store.jobs)
    assert webhook_job.status == "queued"


def test_worker_releases_repository_branch_lock_after_success() -> None:
    service = RepoRagSyncService()
    request = PipelineRequest(
        repository="team/repo",
        files=[RepoFile(path="app.py", content="def run(): pass\n")],
    )
    first_job = service.producer.enqueue_manual(request)

    service.worker.run(first_job.id)
    second_job = service.producer.enqueue_schedule(request)

    assert second_job.id != first_job.id
    assert service.store.running_job_ids_by_lock_key == {}


def test_cleanup_hard_deletes_inactive_rows_in_batches() -> None:
    service = RepoRagSyncService()

    service.run(
        sync_request(
            "team/repo",
            [
                RepoFile(path="app.py", content="def run():\n    return False\n"),
                RepoFile(path="docs.md", content="# Old docs\n"),
            ],
        )
    )
    service.run(
        sync_request(
            "team/repo",
            [RepoFile(path="app.py", content="def run():\n    return True\n")],
        )
    )

    inactive_rows = sum(1 for chunk in service.store.chunks.values() if not chunk.is_active)
    assert inactive_rows == 2

    deleted = service.cleanup.cleanup(batch_size=1, cutoff=datetime.now(UTC))

    assert deleted == 1
    assert sum(1 for chunk in service.store.chunks.values() if not chunk.is_active) == 1
