# draft chunk를 저장/응답에 사용할 evidence chunk DTO로 변환하는 파일
# chunk id, hash, citation 같은 식별 정보를 조립
from app.domains.github.schema import GitHubFileSnapshotDTO
from app.domains.rag.chunk_citation import ChunkCitationService
from app.domains.rag.chunk_identity import ChunkIdentityService
from app.domains.rag.schema import (
    RagEvidenceChunkDraftDTO,
    RagEvidenceChunkDTO,
)


# evidence chunk factory
class ChunkFactory:
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


# default chunk factory
DEFAULT_CHUNK_FACTORY = ChunkFactory(
    identity=ChunkIdentityService(),
    citation=ChunkCitationService(),
)
