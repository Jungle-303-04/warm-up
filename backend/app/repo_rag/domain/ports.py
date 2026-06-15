"""repo-rag 포트(인터페이스) 정의.

포트는 도메인이 소유하고, 어댑터(infrastructure)가 이를 구현한다.
이렇게 두면 application/도메인이 구체 기술이 아니라 추상에만 의존한다(DIP).
"""

from datetime import datetime
from typing import Protocol, runtime_checkable

from app.pipeline.api.schemas import RepoSnapshot, RetrievalChunk
from app.repo_rag.api.schemas import RepoFileChange, RepoRagSyncRequest
from app.repo_rag.domain.records import (
    ChunkRecord,
    EmbeddedChunk,
    FileRecord,
    RepositoryRecord,
    SnapshotRecord,
    SyncEventRecord,
    SyncJobRecord,
)
from app.repo_rag.domain.retrieval import SearchHit


@runtime_checkable
class EmbeddingClient(Protocol):
    """청크 텍스트를 임베딩 벡터로 변환하는 포트."""

    @property
    def model(self) -> str: ...

    @property
    def dimension(self) -> int: ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class RepoRagStore(Protocol):
    """repo-rag 영속 저장소 포트."""

    def create_job(self, request: RepoRagSyncRequest) -> SyncJobRecord: ...

    def claim_next_queued_job(self) -> SyncJobRecord | None: ...

    def get_job(self, job_id: str) -> SyncJobRecord: ...

    def start_job(self, job_id: str) -> SyncJobRecord: ...

    def claim_job_lock(self, job_id: str) -> None: ...

    def release_job_lock(self, job_id: str) -> None: ...

    def attach_job_repository(self, job_id: str, repository_id: str) -> None: ...

    def finish_job(self, job_id: str) -> SyncJobRecord: ...

    def fail_job(self, job_id: str, error: str) -> SyncJobRecord: ...

    def record_event(self, job_id: str, stage: str, detail: str) -> SyncEventRecord: ...

    def job_events(self, job_id: str) -> list[SyncEventRecord]: ...

    def upsert_repository(
        self,
        request: RepoRagSyncRequest,
        snapshot: RepoSnapshot,
    ) -> RepositoryRecord: ...

    def find_repository_id(self, source_key: str) -> str | None: ...

    def active_files(self, repository_id: str) -> dict[str, FileRecord]: ...

    def record_snapshot(
        self,
        repository_id: str,
        snapshot: RepoSnapshot,
    ) -> SnapshotRecord: ...

    def apply_file_changes(
        self,
        repository_id: str,
        snapshot_id: str,
        snapshot: RepoSnapshot,
        changes: list[RepoFileChange],
    ) -> dict[str, FileRecord]: ...

    def upsert_chunks(
        self,
        repository_id: str,
        snapshot_id: str,
        file_records: dict[str, FileRecord],
        chunks: list[EmbeddedChunk],
    ) -> list[ChunkRecord]: ...

    def active_chunks(self, repository_id: str) -> list[RetrievalChunk]: ...

    def hard_delete_inactive(self, batch_size: int, cutoff: datetime) -> int: ...


class RepoRagRetriever(Protocol):
    """하이브리드 검색 포트."""

    def search(self, repository_id: str, query: str, limit: int) -> list[SearchHit]: ...
