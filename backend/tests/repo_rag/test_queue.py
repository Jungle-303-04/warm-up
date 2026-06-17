from app.pipeline.router import RepoFile
from app.repo_rag.api.schemas import RepoRagSyncRequest
from app.repo_rag.infrastructure.in_memory_store import InMemoryRepoRagStore


def _request(repository: str) -> RepoRagSyncRequest:
    return RepoRagSyncRequest(
        repository=repository,
        branch="main",
        files=[RepoFile(path="app.py", content="def run():\n    return True\n")],
    )


def test_claim_returns_none_when_empty() -> None:
    store = InMemoryRepoRagStore()
    assert store.claim_next_queued_job() is None


def test_claim_marks_job_running() -> None:
    store = InMemoryRepoRagStore()
    job = store.create_job(_request("team/a"))

    claimed = store.claim_next_queued_job()

    assert claimed is not None
    assert claimed.id == job.id
    assert store.get_job(job.id).status == "running_sync"


def test_claim_skips_already_claimed_job() -> None:
    store = InMemoryRepoRagStore()
    store.create_job(_request("team/a"))

    first = store.claim_next_queued_job()
    second = store.claim_next_queued_job()  # 더 이상 queued 없음

    assert first is not None
    assert second is None


def test_claim_returns_oldest_first() -> None:
    store = InMemoryRepoRagStore()
    older = store.create_job(_request("team/a"))
    store.create_job(_request("team/b"))

    claimed = store.claim_next_queued_job()

    assert claimed is not None
    assert claimed.id == older.id
