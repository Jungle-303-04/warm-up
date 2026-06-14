# RAG chunk의 id와 hash를 만드는 파일
# 같은 파일/commit/content 기준으로 chunk를 안정적으로 식별
from app.common.identity import hash_text
from app.domains.github.api.schema import GitHubFileSnapshotDTO
from app.domains.rag.api.schema import RagEvidenceChunkDraftDTO


CHUNK_HASH_LENGTH = 16


# chunk identity builder
class ChunkIdentityService:
    def build_hash(
        self,
        file_snapshot: GitHubFileSnapshotDTO,
        chunk: RagEvidenceChunkDraftDTO,
    ) -> str:
        raw_identity = "\0".join(
            [
                file_snapshot.path,
                file_snapshot.content_hash,
                chunk.chunk_type,
                chunk.symbol_name or "",
                chunk.chunk_text,
            ]
        )
        return hash_text(raw_identity)[:CHUNK_HASH_LENGTH]

    def build_id(self, file_snapshot: GitHubFileSnapshotDTO, chunk_hash: str) -> str:
        return f"{file_snapshot.path}@{file_snapshot.commit_sha}:{chunk_hash}"


# default identity service
DEFAULT_CHUNK_IDENTITY_SERVICE = ChunkIdentityService()


# legacy helper functions
def build_chunk_hash(
    file_snapshot: GitHubFileSnapshotDTO,
    chunk: RagEvidenceChunkDraftDTO,
) -> str:
    return DEFAULT_CHUNK_IDENTITY_SERVICE.build_hash(file_snapshot, chunk)


def build_chunk_id(file_snapshot: GitHubFileSnapshotDTO, chunk_hash: str) -> str:
    return DEFAULT_CHUNK_IDENTITY_SERVICE.build_id(file_snapshot, chunk_hash)
