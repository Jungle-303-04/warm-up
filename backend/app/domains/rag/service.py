from app.domains.rag.chunk_identity import (
    build_chunk_citation,
    build_chunk_hash,
    build_chunk_id,
)
from app.domains.rag.chunking import (
    build_minimal_evidence_chunks,
    text_splitter,
)
from app.domains.rag.python_classifier import (
    classify_python_chunk,
    detect_python_chunk_type,
)
from langchain_openai import OpenAIEmbeddings


EMBEDDING_MODEL_NAME = "text-embedding-3-large"


def create_embedding_model():
    return OpenAIEmbeddings(model=EMBEDDING_MODEL_NAME)


__all__ = [
    "build_chunk_citation",
    "build_chunk_hash",
    "build_chunk_id",
    "build_minimal_evidence_chunks",
    "classify_python_chunk",
    "create_embedding_model",
    "detect_python_chunk_type",
    "text_splitter",
]
