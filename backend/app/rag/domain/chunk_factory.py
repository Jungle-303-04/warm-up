from app.github.api.schema import GitHubFileSnapshotDTO
from app.rag.api.schema import RagEvidenceChunkDraftDTO, RagEvidenceChunkDTO
from app.rag.domain.chunk_citation import ChunkCitationService
from app.rag.domain.chunk_identity import ChunkIdentityService


class ChunkFactory:
    """언어별 draft chunk에 id, hash, citation을 붙여 저장 가능한 evidence chunk로 만든다."""

    def __init__(
        self,
        identity: ChunkIdentityService,
        citation: ChunkCitationService,
    ) -> None:
        self.identity = identity
        self.citation = citation

    def build_many(
        self,
        file_snapshot: GitHubFileSnapshotDTO,
        draft_chunks: list[RagEvidenceChunkDraftDTO],
    ) -> list[RagEvidenceChunkDTO]:
        """파일 하나에서 나온 draft 목록에 안정적인 순번을 부여해 일괄 변환한다."""

        return [
            self.build_one(
                file_snapshot=file_snapshot,
                draft_chunk=draft_chunk,
                chunk_index=index,
            )
            for index, draft_chunk in enumerate(draft_chunks)
        ]

    def build_one(
        self,
        file_snapshot: GitHubFileSnapshotDTO,
        draft_chunk: RagEvidenceChunkDraftDTO,
        chunk_index: int,
    ) -> RagEvidenceChunkDTO:
        """검색과 출처 표시가 가능한 최종 RAG 근거 DTO 하나를 조립한다."""

        chunk_hash = self.identity.build_hash(file_snapshot, draft_chunk)
        return RagEvidenceChunkDTO(
            id=self.identity.build_id(file_snapshot, chunk_hash),
            chunk_hash=chunk_hash,
            citation=self.citation.build_citation(file_snapshot, draft_chunk),
            chunk_index=chunk_index,
            path=file_snapshot.path,
            commit_sha=file_snapshot.commit_sha,
            language=file_snapshot.language,
            source_type=file_snapshot.source_type,
            chunk_text=draft_chunk.chunk_text,
            start_line=draft_chunk.start_line,
            end_line=draft_chunk.end_line,
            symbol_name=draft_chunk.symbol_name,
            chunk_type=draft_chunk.chunk_type,
            metadata=draft_chunk.metadata,
        )


DEFAULT_CHUNK_FACTORY = ChunkFactory(
    identity=ChunkIdentityService(),
    citation=ChunkCitationService(),
)
