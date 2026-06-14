from dataclasses import dataclass

from app.github.api.schema import GitHubFileSnapshotDTO
from app.rag.api.schema import (
    GitHubRagPipelineRequestDTO,
    GitHubRagPipelineResultDTO,
    GitHubRagPipelineSummaryDTO,
    GitHubRagSkippedFileDTO,
    RagEvidenceChunkDTO,
)
from app.rag.service.ports import Chunker, SnapshotBuilder


UNSUPPORTED_RAG_FILE_REASON = "unsupported file type for RAG MVP"


@dataclass(frozen=True)
class RagPipelineArtifacts:
    """파일 순회 중 생기는 snapshot, chunk, skip 기록을 최종 응답 전까지 모아둔다."""

    file_snapshots: list[GitHubFileSnapshotDTO]
    evidence_chunks: list[RagEvidenceChunkDTO]
    skipped_files: list[GitHubRagSkippedFileDTO]


class GitHubRagPipelineService:
    """GitHub 파일 응답을 RAG 저장에 필요한 snapshot과 evidence chunk로 변환한다."""

    def __init__(
        self,
        snapshot_builder: SnapshotBuilder,
        chunking_service: Chunker,
    ) -> None:
        self.snapshot_builder = snapshot_builder
        self.chunking_service = chunking_service

    def build_index_from_github_files(
        self,
        request: GitHubRagPipelineRequestDTO,
    ) -> GitHubRagPipelineResultDTO:
        """파일 목록을 분석한 뒤 저장소가 바로 쓸 수 있는 파이프라인 결과 DTO를 만든다."""

        artifacts = self.collect_artifacts(request)

        return GitHubRagPipelineResultDTO(
            commit_sha=request.commit_sha,
            file_snapshots=artifacts.file_snapshots,
            evidence_chunks=artifacts.evidence_chunks,
            skipped_files=artifacts.skipped_files,
            summary=build_pipeline_summary(
                total_files=len(request.files),
                indexed_files=len(artifacts.file_snapshots),
                skipped_files=len(artifacts.skipped_files),
                total_chunks=len(artifacts.evidence_chunks),
            ),
        )

    def collect_artifacts(
        self,
        request: GitHubRagPipelineRequestDTO,
    ) -> RagPipelineArtifacts:
        """파일별 실패가 전체 분석을 중단하지 않도록 성공/스킵 결과를 따로 누적한다."""

        file_snapshots: list[GitHubFileSnapshotDTO] = []
        evidence_chunks: list[RagEvidenceChunkDTO] = []
        skipped_files: list[GitHubRagSkippedFileDTO] = []

        for file_response in request.files:
            try:
                file_snapshot = self.snapshot_builder.build(
                    file_response=file_response,
                    commit_sha=request.commit_sha,
                )
                file_chunks = self.chunking_service.build_minimal_evidence_chunks(
                    file_snapshot
                )
            except ValueError as exc:
                skipped_files.append(
                    GitHubRagSkippedFileDTO(
                        path=file_response.path,
                        reason=str(exc),
                    )
                )
                continue

            if not file_chunks:
                skipped_files.append(
                    GitHubRagSkippedFileDTO(
                        path=file_snapshot.path,
                        reason=UNSUPPORTED_RAG_FILE_REASON,
                    )
                )
                continue

            file_snapshots.append(file_snapshot)
            evidence_chunks.extend(file_chunks)

        return RagPipelineArtifacts(
            file_snapshots=file_snapshots,
            evidence_chunks=evidence_chunks,
            skipped_files=skipped_files,
        )


def build_pipeline_summary(
    total_files: int,
    indexed_files: int,
    skipped_files: int,
    total_chunks: int,
) -> GitHubRagPipelineSummaryDTO:
    """인덱싱 결과 화면과 run 메타데이터에 공통으로 쓰는 집계 DTO를 만든다."""

    return GitHubRagPipelineSummaryDTO(
        total_files=total_files,
        indexed_files=indexed_files,
        skipped_files=skipped_files,
        total_chunks=total_chunks,
    )
