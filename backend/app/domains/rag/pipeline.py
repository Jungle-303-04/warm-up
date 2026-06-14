from app.domains.github.service import build_file_snapshot_from_github_response
from app.domains.github.schema import GitHubFileSnapshotDTO
from app.domains.rag.schema import (
    GitHubRagPipelineRequestDTO,
    GitHubRagPipelineResultDTO,
    GitHubRagPipelineSummaryDTO,
    GitHubRagSkippedFileDTO,
    RagEvidenceChunkDTO,
)
from app.domains.rag.service import build_minimal_evidence_chunks


UNSUPPORTED_RAG_FILE_REASON = "unsupported file type for RAG MVP"


class GitHubRagPipelineService:
    def build_index_from_github_files(
        self,
        request: GitHubRagPipelineRequestDTO,
    ) -> GitHubRagPipelineResultDTO:
        file_snapshots: list[GitHubFileSnapshotDTO] = []
        evidence_chunks: list[RagEvidenceChunkDTO] = []
        skipped_files: list[GitHubRagSkippedFileDTO] = []

        for file_response in request.files:
            try:
                file_snapshot = build_file_snapshot_from_github_response(
                    file_response=file_response,
                    commit_sha=request.commit_sha,
                )
                file_chunks = build_minimal_evidence_chunks(file_snapshot)
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

        return GitHubRagPipelineResultDTO(
            commit_sha=request.commit_sha,
            file_snapshots=file_snapshots,
            evidence_chunks=evidence_chunks,
            skipped_files=skipped_files,
            summary=build_pipeline_summary(
                total_files=len(request.files),
                indexed_files=len(file_snapshots),
                skipped_files=len(skipped_files),
                total_chunks=len(evidence_chunks),
            ),
        )


def build_pipeline_summary(
    total_files: int,
    indexed_files: int,
    skipped_files: int,
    total_chunks: int,
) -> GitHubRagPipelineSummaryDTO:
    return GitHubRagPipelineSummaryDTO(
        total_files=total_files,
        indexed_files=indexed_files,
        skipped_files=skipped_files,
        total_chunks=total_chunks,
    )
