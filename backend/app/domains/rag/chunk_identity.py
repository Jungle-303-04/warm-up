from app.common.identity import hash_text
from app.domains.github.schema import GitHubFileSnapshotDTO
from app.domains.rag.schema import RagEvidenceChunkDraftDTO


CHUNK_HASH_LENGTH = 16


def build_chunk_hash(
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


def build_chunk_id(file_snapshot: GitHubFileSnapshotDTO, chunk_hash: str) -> str:
    return f"{file_snapshot.path}@{file_snapshot.commit_sha}:{chunk_hash}"


def build_chunk_citation(
    file_snapshot: GitHubFileSnapshotDTO,
    chunk: RagEvidenceChunkDraftDTO,
) -> str:
    if chunk.start_line is None:
        return file_snapshot.citation

    line_range = str(chunk.start_line)
    if chunk.end_line is not None and chunk.end_line != chunk.start_line:
        line_range = f"{chunk.start_line}-{chunk.end_line}"

    return f"{file_snapshot.path}:{line_range}@{file_snapshot.commit_sha}"
