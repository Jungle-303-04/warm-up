# RAG chunk가 원본 파일의 어느 위치에서 왔는지 citation을 만드는 파일
# line 정보가 있으면 path:line@commit 형태로 만들어 검색 결과 근거에 사용
from app.domains.github.schema import GitHubFileSnapshotDTO
from app.domains.rag.schema import RagEvidenceChunkDraftDTO


# evidence chunk citation builder
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


# default citation service
DEFAULT_CHUNK_CITATION_SERVICE = ChunkCitationService()


# legacy helper function
def build_chunk_citation(
    file_snapshot: GitHubFileSnapshotDTO,
    chunk: RagEvidenceChunkDraftDTO,
) -> str:
    return DEFAULT_CHUNK_CITATION_SERVICE.build_citation(file_snapshot, chunk)
