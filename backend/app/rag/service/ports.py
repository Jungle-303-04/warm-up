from typing import Any, Protocol

from sqlalchemy.orm import Session

from app.github.api.schema import GitHubFileResponseDTO, GitHubFileSnapshotDTO
from app.rag.api.schema import (
    GitHubRagPipelineRequestDTO,
    GitHubRagPipelineResultDTO,
    GitHubRepositoryIndexRequestDTO,
    RagAskRequestDTO,
    RagAskResponseDTO,
    RagEvidenceChunkDTO,
    RagIndexRunDetailDTO,
    RagIndexRunListResponseDTO,
    RagSqlChunkSearchResponseDTO,
    RagStoredIndexResponseDTO,
    RagVectorSearchRequestDTO,
    RagVectorSearchResponseDTO,
)


class IndexUseCase(Protocol):
    def index_repository_and_store(
        self,
        db: Session,
        request: GitHubRepositoryIndexRequestDTO,
        github_access_token: str,
    ) -> RagStoredIndexResponseDTO: ...

    def index_and_store(
        self,
        db: Session,
        request: GitHubRagPipelineRequestDTO,
    ) -> RagStoredIndexResponseDTO: ...

    def list_runs(self, db: Session, limit: int = 20) -> RagIndexRunListResponseDTO: ...

    def get_run_detail(self, db: Session, run_id: int) -> RagIndexRunDetailDTO | None: ...

    def search_sql_chunks(
        self,
        db: Session,
        keyword: str,
        limit: int,
    ) -> RagSqlChunkSearchResponseDTO: ...

    def search_vector_chunks(
        self,
        request: RagVectorSearchRequestDTO,
    ) -> RagVectorSearchResponseDTO: ...


class AnswerUseCase(Protocol):
    def answer(self, db: Session, request: RagAskRequestDTO) -> RagAskResponseDTO: ...


class AnswerGraph(Protocol):
    def run(self, request: RagAskRequestDTO, index_run: Any) -> RagAskResponseDTO: ...


class RepoSource(Protocol):
    def build_pipeline_request_from_repository(
        self,
        access_token: str,
        request: GitHubRepositoryIndexRequestDTO,
    ) -> GitHubRagPipelineRequestDTO: ...


class IndexPipeline(Protocol):
    def build_index_from_github_files(
        self,
        request: GitHubRagPipelineRequestDTO,
    ) -> GitHubRagPipelineResultDTO: ...


class RagStore(Protocol):
    def save_pipeline_result(
        self,
        db: Session,
        request: GitHubRagPipelineRequestDTO,
        result: GitHubRagPipelineResultDTO,
    ) -> Any: ...

    def count_chunks_by_run_id(self, db: Session, run_id: int) -> int: ...

    def count_runs(self, db: Session) -> int: ...

    def list_runs(self, db: Session, limit: int = 20) -> list[Any]: ...

    def get_run(self, db: Session, run_id: int) -> Any | None: ...

    def list_file_snapshots(
        self,
        db: Session,
        run_id: int,
    ) -> list[Any]: ...

    def list_chunks(self, db: Session, run_id: int) -> list[Any]: ...

    def list_skipped_files(self, db: Session, run_id: int) -> list[Any]: ...

    def search_chunks_by_keyword(
        self,
        db: Session,
        keyword: str,
        limit: int = 10,
    ) -> list[Any]: ...

    def find_latest_run(
        self,
        db: Session,
        repository_full_name: str,
        branch: str | None = None,
        commit_sha: str | None = None,
    ) -> Any | None: ...


class VectorStore(Protocol):
    collection_name: str

    def save_chunks(
        self,
        chunks: list[RagEvidenceChunkDTO],
        run_id: int,
        repository_full_name: str | None = None,
        branch: str | None = None,
    ) -> int: ...

    def count(self) -> int: ...

    def search(
        self,
        query: str,
        limit: int = 5,
        run_id: int | None = None,
        repository_full_name: str | None = None,
        branch: str | None = None,
        commit_sha: str | None = None,
    ) -> dict: ...


class SnapshotBuilder(Protocol):
    def build(
        self,
        file_response: GitHubFileResponseDTO,
        commit_sha: str,
    ) -> GitHubFileSnapshotDTO: ...


class Chunker(Protocol):
    def build_minimal_evidence_chunks(
        self,
        file_snapshot: GitHubFileSnapshotDTO,
    ) -> list[RagEvidenceChunkDTO]: ...


class LlmClient(Protocol):
    def answer_with_evidence(
        self,
        question: str,
        documents: list[str],
        metadatas: list[dict],
    ) -> str: ...


class PromptBuilder(Protocol):
    def build_messages(
        self,
        question: str,
        documents: list[str],
        metadatas: list[dict],
    ) -> list[dict[str, str]]: ...


class EvidenceFormatter(Protocol):
    def format(
        self,
        documents: list[str],
        metadatas: list[dict],
    ) -> str: ...


class TextGenerator(Protocol):
    def generate(self, messages: list[dict[str, Any]]) -> str: ...
