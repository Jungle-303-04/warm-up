from dataclasses import dataclass, field

from app.repo_rag.cleanup import RetentionCleanupService
from app.repo_rag.in_memory_store import InMemoryRepoRagStore
from app.repo_rag.producer import SyncJobProducer
from app.repo_rag.schemas import RepoRagSyncRequest, RepoRagSyncResponse
from app.repo_rag.store import RepoRagStore
from app.repo_rag.worker import SyncWorker


@dataclass(slots=True)
class RepoRagSyncService:
    store: RepoRagStore = field(default_factory=InMemoryRepoRagStore)
    producer: SyncJobProducer = field(init=False)
    worker: SyncWorker = field(init=False)
    cleanup: RetentionCleanupService = field(init=False)

    def __post_init__(self) -> None:
        self.producer = SyncJobProducer(self.store)
        self.worker = SyncWorker(self.store)
        self.cleanup = RetentionCleanupService(self.store)

    def run(self, request: RepoRagSyncRequest) -> RepoRagSyncResponse:
        job = self.producer.enqueue(request)
        return self.worker.run(job.id)
