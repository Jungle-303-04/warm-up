from app.domains.github.schema import GitHubFileSnapshotDTO
from app.domains.rag.schema import RagEvidenceChunkDraftDTO


class ChunkCitationService:
    def build_citation(
        self,
        file_snapshot: GitHubFileSnapshotDTO,
        chunk: RagEvidenceChunkDraftDTO,
    ) -> str:
        if chunk.start_line is None:
            return file_snapshot.citation

        line_range = str(chunk.start_line)
        if chunk.end_line is not None and chunk.end_line != chunk.start_line:
            line_range = f"{chunk.start_line}-{chunk.end_line}"

        return f"{file_snapshot.path}:{line_range}@{file_snapshot.commit_sha}"


DEFAULT_CHUNK_CITATION_SERVICE = ChunkCitationService()


def build_chunk_citation(
    file_snapshot: GitHubFileSnapshotDTO,
    chunk: RagEvidenceChunkDraftDTO,
) -> str:
    return DEFAULT_CHUNK_CITATION_SERVICE.build_citation(file_snapshot, chunk)
