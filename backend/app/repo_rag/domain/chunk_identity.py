from dataclasses import dataclass

from app.repo_rag.domain.identity import hash_text

CHUNK_HASH_LENGTH = 16


@dataclass(slots=True)
class FileContext:
    """청킹 대상 파일의 식별 정보."""

    repository: str
    path: str
    commit_sha: str
    content_hash: str
    content: str
    language: str
    source_type: str = "github_file"


@dataclass(slots=True)
class ChunkDraft:
    """식별자/인용이 붙기 전의 청크 초안."""

    text: str
    chunk_type: str
    start_line: int | None = None
    end_line: int | None = None
    symbol_name: str | None = None


def build_chunk_hash(file_context: FileContext, draft: ChunkDraft) -> str:
    raw_identity = "\0".join(
        [
            file_context.path,
            file_context.content_hash,
            draft.chunk_type,
            draft.symbol_name or "",
            draft.text,
        ]
    )
    return hash_text(raw_identity)[:CHUNK_HASH_LENGTH]


def build_chunk_id(file_context: FileContext, chunk_hash: str) -> str:
    return f"{file_context.path}@{file_context.commit_sha}:{chunk_hash}"


def build_chunk_citation(file_context: FileContext, draft: ChunkDraft) -> str:
    base = f"{file_context.repository}:{file_context.path}"

    if draft.start_line is None:
        return f"{base}@{file_context.commit_sha}"

    line_range = str(draft.start_line)
    if draft.end_line is not None and draft.end_line != draft.start_line:
        line_range = f"{draft.start_line}-{draft.end_line}"

    return f"{base}:{line_range}@{file_context.commit_sha}"
