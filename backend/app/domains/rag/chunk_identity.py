from app.common.identity import hash_text
from app.domains.github.schema import GitHubFileSnapshotDTO
from app.domains.rag.schema import RagEvidenceChunkDraftDTO


CHUNK_HASH_LENGTH = 16


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


DEFAULT_CHUNK_IDENTITY_SERVICE = ChunkIdentityService()


def build_chunk_hash(
    file_snapshot: GitHubFileSnapshotDTO,
    chunk: RagEvidenceChunkDraftDTO,
) -> str:
    return DEFAULT_CHUNK_IDENTITY_SERVICE.build_hash(file_snapshot, chunk)


def build_chunk_id(file_snapshot: GitHubFileSnapshotDTO, chunk_hash: str) -> str:
    return DEFAULT_CHUNK_IDENTITY_SERVICE.build_id(file_snapshot, chunk_hash)
