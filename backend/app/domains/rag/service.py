# RAG domain의 기존 import 경로를 유지하기 위한 service facade 파일
# 실제 구현은 chunking, chunk_identity, python_classifier 등으로 분리
from app.domains.rag.chunk_identity import (
    ChunkIdentityService as ChunkIdentityService,
    build_chunk_hash as build_chunk_hash,
    build_chunk_id as build_chunk_id,
)
from app.domains.rag.chunk_citation import (
    ChunkCitationService as ChunkCitationService,
    build_chunk_citation as build_chunk_citation,
)
from app.domains.rag.chunking import (
    ChunkerRegistry as ChunkerRegistry,
    ChunkFactory as ChunkFactory,
    ChunkingService as ChunkingService,
    LanguageChunker as LanguageChunker,
    MarkdownChunker as MarkdownChunker,
    PythonChunker as PythonChunker,
    SnapshotValidator as SnapshotValidator,
)
from app.domains.rag.python_classifier import (
    classify_python_chunk as classify_python_chunk,
    detect_python_chunk_type as detect_python_chunk_type,
)
from langchain_openai import OpenAIEmbeddings


EMBEDDING_MODEL_NAME = "text-embedding-3-large"


# embedding model factory
def create_embedding_model() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=EMBEDDING_MODEL_NAME)


__all__ = [
    "build_chunk_citation",
    "build_chunk_hash",
    "build_chunk_id",
    "classify_python_chunk",
    "create_embedding_model",
    "detect_python_chunk_type",
    "ChunkCitationService",
    "ChunkerRegistry",
    "ChunkFactory",
    "ChunkIdentityService",
    "ChunkingService",
    "LanguageChunker",
    "MarkdownChunker",
    "PythonChunker",
    "SnapshotValidator",
]
