from sqlalchemy.orm import Session

from app.domains.rag.pipeline import GitHubRagPipelineService
from app.domains.rag.repository import RagSqlRepository
from app.domains.rag.schema import (
    GitHubRagPipelineRequestDTO,
    RagChunkRecordDTO,
    RagFileSnapshotRecordDTO,
    RagIndexRunDTO,
    RagIndexRunDetailDTO,
    RagIndexRunListResponseDTO,
    RagSkippedFileRecordDTO,
    RagSqlChunkSearchResponseDTO,
    RagStoredIndexResponseDTO,
    RagVectorSearchItemDTO,
    RagVectorSearchRequestDTO,
    RagVectorSearchResponseDTO,
)
from app.domains.rag.vector_repository import RagVectorRepository


class RagIndexService:
    def __init__(
        self,
        pipeline_service: GitHubRagPipelineService,
        sql_repository: RagSqlRepository,
        vector_repository: RagVectorRepository,
    ) -> None:
        self.pipeline_service = pipeline_service
        self.sql_repository = sql_repository
        self.vector_repository = vector_repository

    def index_and_store(
        self,
        db: Session,
        request: GitHubRagPipelineRequestDTO,
    ) -> RagStoredIndexResponseDTO:
        pipeline_result = self.pipeline_service.build_index_from_github_files(request)
        run = self.sql_repository.save_pipeline_result(db, request, pipeline_result)
        vector_chunk_count = self.vector_repository.save_chunks(
            chunks=pipeline_result.evidence_chunks,
            run_id=run.id,
        )

        return RagStoredIndexResponseDTO(
            run_id=run.id,
            vector_collection=self.vector_repository.collection_name,
            sql_chunk_count=self.sql_repository.count_chunks_by_run_id(db, run.id),
            vector_chunk_count=vector_chunk_count,
            pipeline_result=pipeline_result,
        )

    def list_runs(self, db: Session, limit: int = 20) -> RagIndexRunListResponseDTO:
        runs = self.sql_repository.list_runs(db, limit)

        return RagIndexRunListResponseDTO(
            items=[RagIndexRunDTO.model_validate(run) for run in runs],
            total=self.sql_repository.count_runs(db),
        )

    def get_run_detail(self, db: Session, run_id: int) -> RagIndexRunDetailDTO | None:
        run = self.sql_repository.get_run(db, run_id)

        if run is None:
            return None

        return RagIndexRunDetailDTO(
            run=RagIndexRunDTO.model_validate(run),
            file_snapshots=[
                RagFileSnapshotRecordDTO.model_validate(file_snapshot)
                for file_snapshot in self.sql_repository.list_file_snapshots(db, run_id)
            ],
            chunks=[
                RagChunkRecordDTO.model_validate(chunk)
                for chunk in self.sql_repository.list_chunks(db, run_id)
            ],
            skipped_files=[
                RagSkippedFileRecordDTO.model_validate(skipped_file)
                for skipped_file in self.sql_repository.list_skipped_files(db, run_id)
            ],
        )

    def search_sql_chunks(
        self,
        db: Session,
        keyword: str,
        limit: int,
    ) -> RagSqlChunkSearchResponseDTO:
        chunks = self.sql_repository.search_chunks_by_keyword(db, keyword, limit)

        return RagSqlChunkSearchResponseDTO(
            keyword=keyword,
            limit=limit,
            items=[RagChunkRecordDTO.model_validate(chunk) for chunk in chunks],
        )

    def search_vector_chunks(
        self,
        request: RagVectorSearchRequestDTO,
    ) -> RagVectorSearchResponseDTO:
        result = self.vector_repository.search(request.query, request.limit)

        return RagVectorSearchResponseDTO(
            collection=self.vector_repository.collection_name,
            count=self.vector_repository.count(),
            query=request.query,
            items=self.build_vector_search_items(result),
        )

    def build_vector_search_items(self, result: dict) -> list[RagVectorSearchItemDTO]:
        ids = result.get("ids", [[]])[0] or []
        documents = result.get("documents", [[]])[0] or []
        metadatas = result.get("metadatas", [[]])[0] or []
        distances = result.get("distances", [[]])[0] or []

        return [
            RagVectorSearchItemDTO(
                id=chunk_id,
                document=get_list_value(documents, index, ""),
                metadata=get_list_value(metadatas, index, {}) or {},
                distance=get_list_value(distances, index, None),
            )
            for index, chunk_id in enumerate(ids)
        ]


def get_list_value(values: list, index: int, default):
    if index >= len(values):
        return default

    return values[index]
