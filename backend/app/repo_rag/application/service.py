from dataclasses import dataclass

from app.repo_rag.api.schemas import RepoRagSyncRequest, RepoRagSyncResponse
from app.repo_rag.application.indexing import IndexingService
from app.repo_rag.application.producer import SyncJobProducer
from app.repo_rag.application.types import UowFactory
from app.repo_rag.application.unit_of_work import UnitOfWork
from app.repo_rag.application.worker import SyncWorker
from app.repo_rag.domain.ports import EmbeddingClient
from app.repo_rag.domain.records import SyncJobRecord


@dataclass(slots=True)
class RepoRagSyncService:
    """sync 유스케이스. 트랜잭션 경계는 uow_factory()가 만든 with 블록이다."""

    uow_factory: UowFactory
    embedder: EmbeddingClient | None = None

    def run(self, request: RepoRagSyncRequest) -> RepoRagSyncResponse:
        """동기 실행(in-memory/개발용): 큐잉+처리를 한 트랜잭션에서."""
        with self.uow_factory() as uow:
            job = SyncJobProducer(uow.repo_rag).enqueue(request)
            return self._worker(uow).run(job.id)

    def enqueue(self, request: RepoRagSyncRequest) -> SyncJobRecord:
        """큐잉만(Postgres 백그라운드 경로)."""
        with self.uow_factory() as uow:
            return SyncJobProducer(uow.repo_rag).enqueue(request)

    def process(self, job_id: str) -> RepoRagSyncResponse:
        """큐의 job 하나를 처리. 실패 시 별도 트랜잭션으로 실패 사실을 남긴다."""
        try:
            with self.uow_factory() as uow:
                return self._worker(uow).run(job_id)
        except Exception:
            with self.uow_factory() as uow:
                uow.repo_rag.fail_job(job_id, _last_error())
            raise

    def _worker(self, uow: UnitOfWork) -> SyncWorker:
        return SyncWorker(uow.repo_rag, indexing=IndexingService(embedder=self.embedder))


def _last_error() -> str:
    import sys

    exc = sys.exc_info()[1]
    return str(exc) if exc is not None else "unknown error"
