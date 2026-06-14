from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.rag.api.schema import GitHubRagPipelineRequestDTO, GitHubRagPipelineResultDTO
from app.rag.external.model import (
    RagChunk,
    RagFileSnapshot,
    RagIndexRun,
    RagSkippedFile,
)
from app.db.transaction import db_transaction


class RagSqlRepository:
    """RAG 분석 이력과 청크 원문을 SQL에 저장해 정확 검색과 이력 조회를 가능하게 한다."""

    def save_pipeline_result(
        self,
        db: Session,
        request: GitHubRagPipelineRequestDTO,
        result: GitHubRagPipelineResultDTO,
    ) -> RagIndexRun:
        """파이프라인 결과 전체를 하나의 run 기준으로 트랜잭션 저장한다."""

        with db_transaction(db):
            run = self.create_index_run(db, request, result)
            file_snapshot_by_key = self.create_file_snapshots(db, run.id, result)
            self.create_chunks(db, run.id, file_snapshot_by_key, result)
            self.create_skipped_files(db, run.id, result)
            return run

    def create_index_run(
        self,
        db: Session,
        request: GitHubRagPipelineRequestDTO,
        result: GitHubRagPipelineResultDTO,
    ) -> RagIndexRun:
        """분석 단위의 메타데이터와 집계값을 먼저 저장해 다른 테이블의 부모로 사용한다."""

        run = RagIndexRun(
            repository_full_name=request.repository_full_name,
            branch=request.branch,
            commit_sha=request.commit_sha,
            total_files=result.summary.total_files,
            indexed_files=result.summary.indexed_files,
            skipped_files=result.summary.skipped_files,
            total_chunks=result.summary.total_chunks,
        )
        db.add(run)
        db.flush()
        return run

    def create_file_snapshots(
        self,
        db: Session,
        run_id: int,
        result: GitHubRagPipelineResultDTO,
    ) -> dict[tuple[str, str], RagFileSnapshot]:
        """청크가 어떤 파일 스냅샷에서 왔는지 연결할 수 있게 파일 기록을 저장한다."""

        file_snapshot_by_key: dict[tuple[str, str], RagFileSnapshot] = {}

        for snapshot in result.file_snapshots:
            file_snapshot = RagFileSnapshot(
                run_id=run_id,
                path=snapshot.path,
                name=snapshot.name,
                sha=snapshot.sha,
                commit_sha=snapshot.commit_sha,
                language=snapshot.language,
                source_type=snapshot.source_type,
                content_hash=snapshot.content_hash,
                citation=snapshot.citation,
                size=snapshot.size,
                html_url=snapshot.html_url,
            )
            db.add(file_snapshot)
            db.flush()
            file_snapshot_by_key[(snapshot.path, snapshot.commit_sha)] = file_snapshot

        return file_snapshot_by_key

    def create_chunks(
        self,
        db: Session,
        run_id: int,
        file_snapshot_by_key: dict[tuple[str, str], RagFileSnapshot],
        result: GitHubRagPipelineResultDTO,
    ) -> None:
        """LLM 근거 원문과 검색 필터용 metadata를 SQL 청크 테이블에 저장한다."""

        for chunk in result.evidence_chunks:
            file_snapshot = file_snapshot_by_key[(chunk.path, chunk.commit_sha)]
            db.add(
                RagChunk(
                    run_id=run_id,
                    file_snapshot_id=file_snapshot.id,
                    external_chunk_id=chunk.id,
                    chunk_hash=chunk.chunk_hash,
                    chunk_index=chunk.chunk_index,
                    path=chunk.path,
                    commit_sha=chunk.commit_sha,
                    language=chunk.language,
                    source_type=chunk.source_type,
                    chunk_type=chunk.chunk_type,
                    symbol_name=chunk.symbol_name,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    citation=chunk.citation,
                    chunk_text=chunk.chunk_text,
                    metadata_json=chunk.metadata.model_dump(),
                    direct_implementation_evidence=(
                        chunk.metadata.direct_implementation_evidence
                    ),
                )
            )

    def create_skipped_files(
        self,
        db: Session,
        run_id: int,
        result: GitHubRagPipelineResultDTO,
    ) -> None:
        """미지원 파일이나 파싱 실패 파일의 사유를 사용자에게 보여주기 위해 저장한다."""

        db.add_all(
            RagSkippedFile(
                run_id=run_id,
                path=skipped_file.path,
                reason=skipped_file.reason,
            )
            for skipped_file in result.skipped_files
        )

    def count_chunks_by_run_id(self, db: Session, run_id: int) -> int:
        """SQL 저장 청크 수와 벡터 저장 청크 수를 비교할 때 사용한다."""

        return (
            db.scalar(select(func.count()).select_from(RagChunk).where(RagChunk.run_id == run_id))
            or 0
        )

    def count_runs(self, db: Session) -> int:
        """인덱싱 이력 목록의 total 값을 계산한다."""

        return db.scalar(select(func.count()).select_from(RagIndexRun)) or 0

    def list_runs(self, db: Session, limit: int = 20) -> list[RagIndexRun]:
        """최근 분석 이력을 먼저 보여주기 위해 id 역순으로 조회한다."""

        return db.scalars(
            select(RagIndexRun).order_by(RagIndexRun.id.desc()).limit(limit)
        ).all()

    def get_run(self, db: Session, run_id: int) -> RagIndexRun | None:
        """상세 조회 전에 run 존재 여부를 확인한다."""

        return db.get(RagIndexRun, run_id)

    def list_file_snapshots(self, db: Session, run_id: int) -> list[RagFileSnapshot]:
        """특정 run에서 인덱싱된 파일 목록을 재구성한다."""

        return db.scalars(
            select(RagFileSnapshot)
            .where(RagFileSnapshot.run_id == run_id)
            .order_by(RagFileSnapshot.id)
        ).all()

    def list_chunks(self, db: Session, run_id: int) -> list[RagChunk]:
        """특정 run의 청크를 원래 생성 순서대로 보여준다."""

        return db.scalars(
            select(RagChunk)
            .where(RagChunk.run_id == run_id)
            .order_by(RagChunk.chunk_index)
        ).all()

    def list_skipped_files(self, db: Session, run_id: int) -> list[RagSkippedFile]:
        """특정 run에서 제외된 파일과 사유를 보여준다."""

        return db.scalars(
            select(RagSkippedFile)
            .where(RagSkippedFile.run_id == run_id)
            .order_by(RagSkippedFile.id)
        ).all()

    def search_chunks_by_keyword(
        self,
        db: Session,
        keyword: str,
        limit: int = 10,
    ) -> list[RagChunk]:
        """벡터 검색과 별개로 특정 단어가 실제 청크 원문에 있는지 확인한다."""

        return db.scalars(
            select(RagChunk)
            .where(RagChunk.chunk_text.ilike(f"%{keyword}%"))
            .order_by(RagChunk.id.desc())
            .limit(limit)
        ).all()
