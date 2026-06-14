from sqlalchemy.orm import Session

from app.rag.api.schema import (
    GitHubRagPipelineRequestDTO,
    GitHubRepositoryIndexRequestDTO,
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
from app.rag.domain.vector_result import parse_vector_result
from app.rag.service.ports import (
    IndexPipeline,
    RagStore,
    RepoSource,
    VectorStore,
)


class RagIndexService:
    """GitHub 파일 수집 결과를 SQL과 벡터 DB 양쪽에 저장하고 조회하는 유스케이스."""

    def __init__(
        self,
        pipeline_service: IndexPipeline,
        sql_repository: RagStore,
        vector_repository: VectorStore,
        repository_source: RepoSource,
    ) -> None:
        self.pipeline_service = pipeline_service
        self.sql_repository = sql_repository
        self.vector_repository = vector_repository
        self.repository_source = repository_source

    def index_repository_and_store(
        self,
        db: Session,
        request: GitHubRepositoryIndexRequestDTO,
        github_access_token: str,
    ) -> RagStoredIndexResponseDTO:
        """레포지토리 요청을 GitHub 파일 목록 요청으로 바꾼 뒤 인덱싱 저장 흐름을 실행한다."""

        pipeline_request = (
            self.repository_source.build_pipeline_request_from_repository(
                access_token=github_access_token,
                request=request,
            )
        )
        return self.index_and_store(db, pipeline_request)

    def index_and_store(
        self,
        db: Session,
        request: GitHubRagPipelineRequestDTO,
    ) -> RagStoredIndexResponseDTO:
        """파일 스냅샷을 청크로 만든 뒤 SQL 기록과 벡터 검색 데이터를 함께 저장한다."""

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
        """사용자가 과거 분석 이력을 선택할 수 있도록 최근 인덱싱 run을 반환한다."""

        runs = self.sql_repository.list_runs(db, limit)

        return RagIndexRunListResponseDTO(
            items=[RagIndexRunDTO.model_validate(run) for run in runs],
            total=self.sql_repository.count_runs(db),
        )

    def get_run_detail(self, db: Session, run_id: int) -> RagIndexRunDetailDTO | None:
        """특정 분석 run의 파일, 청크, 스킵 사유를 한 화면에서 볼 수 있게 묶는다."""

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
        """정확한 키워드 확인용으로 SQL chunk_text 검색을 제공한다."""

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
        """의미 유사도 기반 근거 확인용으로 벡터 DB 검색 결과를 API DTO로 바꾼다."""

        result = self.vector_repository.search(
            query=request.query,
            limit=request.limit,
            run_id=request.run_id,
        )

        return RagVectorSearchResponseDTO(
            collection=self.vector_repository.collection_name,
            count=self.vector_repository.count(),
            query=request.query,
            items=self.build_vector_search_items(result),
        )

    def build_vector_search_items(self, result: dict) -> list[RagVectorSearchItemDTO]:
        """Chroma 검색 row를 프론트가 보기 쉬운 item DTO로 변환한다."""

        return [
            RagVectorSearchItemDTO(
                id=row.id,
                document=row.document,
                metadata=row.metadata,
                distance=row.distance,
            )
            for row in parse_vector_result(result)
        ]
