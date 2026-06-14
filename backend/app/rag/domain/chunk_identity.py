from app.github.api.schema import GitHubFileSnapshotDTO
from app.rag.api.schema import RagEvidenceChunkDraftDTO
from app.shared.identity import hash_text

CHUNK_HASH_LENGTH = 16


class ChunkIdentityService:
    """같은 코드 조각을 중복 저장하지 않도록 내용 기반 chunk hash와 id를 만든다."""

    def build_hash(
        self,
        file_snapshot: GitHubFileSnapshotDTO,
        chunk: RagEvidenceChunkDraftDTO,
    ) -> str:
        """파일 경로, 내용 hash, symbol 정보를 섞어 청크 내용 변경을 감지한다."""

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
        """파일, commit, chunk hash를 조합해 벡터 DB와 SQL에서 같이 쓸 외부 ID를 만든다."""

        return f"{file_snapshot.path}@{file_snapshot.commit_sha}:{chunk_hash}"


DEFAULT_CHUNK_IDENTITY_SERVICE = ChunkIdentityService()


def build_chunk_hash(
    file_snapshot: GitHubFileSnapshotDTO,
    chunk: RagEvidenceChunkDraftDTO,
) -> str:
    """기존 함수형 호출부가 클래스 구현을 몰라도 hash를 만들 수 있게 한다."""

    return DEFAULT_CHUNK_IDENTITY_SERVICE.build_hash(file_snapshot, chunk)


def build_chunk_id(file_snapshot: GitHubFileSnapshotDTO, chunk_hash: str) -> str:
    """기존 함수형 호출부가 클래스 구현을 몰라도 chunk id를 만들 수 있게 한다."""

    return DEFAULT_CHUNK_IDENTITY_SERVICE.build_id(file_snapshot, chunk_hash)
