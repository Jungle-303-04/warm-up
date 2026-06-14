from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domains.rag.model import (
    RagChunk,
    RagFileSnapshot,
    RagIndexRun,
    RagSkippedFile,
)
from app.domains.rag.schema import GitHubRagPipelineRequestDTO, GitHubRagPipelineResultDTO


class RagSqlRepository:
    def save_pipeline_result(
        self,
        db: Session,
        request: GitHubRagPipelineRequestDTO,
        result: GitHubRagPipelineResultDTO,
    ) -> RagIndexRun:
        run = self.create_index_run(db, request, result)
        file_snapshot_by_key = self.create_file_snapshots(db, run.id, result)
        self.create_chunks(db, run.id, file_snapshot_by_key, result)
        self.create_skipped_files(db, run.id, result)
        db.commit()
        return run

    def create_index_run(
        self,
        db: Session,
        request: GitHubRagPipelineRequestDTO,
        result: GitHubRagPipelineResultDTO,
    ) -> RagIndexRun:
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
        db.add_all(
            RagSkippedFile(
                run_id=run_id,
                path=skipped_file.path,
                reason=skipped_file.reason,
            )
            for skipped_file in result.skipped_files
        )

    def count_chunks_by_run_id(self, db: Session, run_id: int) -> int:
        return (
            db.scalar(select(func.count()).select_from(RagChunk).where(RagChunk.run_id == run_id))
            or 0
        )

    def count_runs(self, db: Session) -> int:
        return db.scalar(select(func.count()).select_from(RagIndexRun)) or 0

    def list_runs(self, db: Session, limit: int = 20) -> list[RagIndexRun]:
        return db.scalars(
            select(RagIndexRun).order_by(RagIndexRun.id.desc()).limit(limit)
        ).all()

    def get_run(self, db: Session, run_id: int) -> RagIndexRun | None:
        return db.get(RagIndexRun, run_id)

    def list_file_snapshots(self, db: Session, run_id: int) -> list[RagFileSnapshot]:
        return db.scalars(
            select(RagFileSnapshot)
            .where(RagFileSnapshot.run_id == run_id)
            .order_by(RagFileSnapshot.id)
        ).all()

    def list_chunks(self, db: Session, run_id: int) -> list[RagChunk]:
        return db.scalars(
            select(RagChunk)
            .where(RagChunk.run_id == run_id)
            .order_by(RagChunk.chunk_index)
        ).all()

    def list_skipped_files(self, db: Session, run_id: int) -> list[RagSkippedFile]:
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
        return db.scalars(
            select(RagChunk)
            .where(RagChunk.chunk_text.ilike(f"%{keyword}%"))
            .order_by(RagChunk.id.desc())
            .limit(limit)
        ).all()
