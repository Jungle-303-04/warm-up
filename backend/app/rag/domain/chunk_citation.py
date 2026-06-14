from app.github.api.schema import GitHubFileSnapshotDTO
from app.rag.api.schema import RagEvidenceChunkDraftDTO


class ChunkCitationService:
    """LLM 답변이 어떤 파일과 줄 범위를 근거로 삼았는지 표시할 citation을 만든다."""

    def build_citation(
        self,
        file_snapshot: GitHubFileSnapshotDTO,
        chunk: RagEvidenceChunkDraftDTO,
    ) -> str:
        """라인 정보가 있으면 path:line@commit, 없으면 파일 단위 citation을 사용한다."""

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
    """기존 함수형 호출부가 클래스 구현을 몰라도 citation을 만들 수 있게 한다."""

    return DEFAULT_CHUNK_CITATION_SERVICE.build_citation(file_snapshot, chunk)
