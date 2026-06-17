from datetime import UTC, datetime

from app.pipeline.router import PipelineRequest, RepoFile
from app.repo_rag.api.schemas import RepoRagSyncRequest
from app.repo_rag.application.cleanup import RetentionCleanupService
from app.repo_rag.application.indexing import IndexingService
from app.repo_rag.application.producer import SyncJobProducer
from app.repo_rag.application.service import RepoRagSyncService
from app.repo_rag.application.unit_of_work import InMemoryUnitOfWork
from app.repo_rag.application.worker import SyncWorker
from app.repo_rag.infrastructure.in_memory_store import InMemoryRepoRagStore


def _service(store: InMemoryRepoRagStore) -> RepoRagSyncService:
    return RepoRagSyncService(uow_factory=lambda: InMemoryUnitOfWork(store))


def sync_request(repository: str, files: list[RepoFile]) -> RepoRagSyncRequest:
    return RepoRagSyncRequest(repository=repository, branch="main", files=files)


def test_manual_sync_persists_job_snapshot_files_chunks_and_events() -> None:
    store = InMemoryRepoRagStore()
    service = _service(store)

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
    assert len(store.snapshots) == 1
    assert len(store.files) == 2
    assert len(store.chunks) == 3


def test_second_sync_detects_diff_and_soft_deletes_inactive_chunks() -> None:
    store = InMemoryRepoRagStore()
    service = _service(store)

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

    inactive_chunks = [chunk for chunk in store.chunks.values() if not chunk.is_active]
    assert {chunk.source_path for chunk in inactive_chunks} == {"app.py", "docs.md"}
    assert all(chunk.deleted_at is not None for chunk in inactive_chunks)


def test_producers_dedupe_active_jobs_for_same_repository_branch() -> None:
    store = InMemoryRepoRagStore()
    producer = SyncJobProducer(store)
    request = PipelineRequest(
        repository="team/repo",
        files=[RepoFile(path="app.py", content="def run(): pass\n")],
    )
    webhook_request = PipelineRequest(
        repository="team/webhook-repo",
        files=[RepoFile(path="app.py", content="def run(): pass\n")],
    )

    manual_job = producer.enqueue_manual(request)
    schedule_job = producer.enqueue_schedule(request)
    webhook_job = producer.enqueue_webhook(webhook_request, requested_commit_sha="abc123")
    duplicate_webhook_job = producer.enqueue_webhook(webhook_request, requested_commit_sha="abc123")

    assert manual_job.id == schedule_job.id
    assert webhook_job.id == duplicate_webhook_job.id
    assert {manual_job.id, webhook_job.id} <= set(store.jobs)
    assert webhook_job.status == "queued"


def test_worker_releases_repository_branch_lock_after_success() -> None:
    store = InMemoryRepoRagStore()
    producer = SyncJobProducer(store)
    worker = SyncWorker(store, indexing=IndexingService())
    request = PipelineRequest(
        repository="team/repo",
        files=[RepoFile(path="app.py", content="def run(): pass\n")],
    )
    first_job = producer.enqueue_manual(request)

    worker.run(first_job.id)
    second_job = producer.enqueue_schedule(request)

    assert second_job.id != first_job.id
    assert store.running_job_ids_by_lock_key == {}


def test_cleanup_hard_deletes_inactive_rows_in_batches() -> None:
    store = InMemoryRepoRagStore()
    service = _service(store)
    cleanup = RetentionCleanupService(store)

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

    inactive_rows = sum(1 for chunk in store.chunks.values() if not chunk.is_active)
    assert inactive_rows == 3

    deleted = cleanup.cleanup(batch_size=1, cutoff=datetime.now(UTC))

    assert deleted == 1
    assert sum(1 for chunk in store.chunks.values() if not chunk.is_active) == 2
