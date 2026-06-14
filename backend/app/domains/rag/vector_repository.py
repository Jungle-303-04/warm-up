import os

import chromadb
from chromadb.api.models.Collection import Collection

from app.domains.rag.embedding import EmbeddingService
from app.domains.rag.schema import RagEvidenceChunkDTO


DEFAULT_CHROMA_PATH = os.getenv("RAG_CHROMA_PATH", ".chroma/rag")
DEFAULT_CHROMA_HOST = os.getenv("RAG_CHROMA_HOST")
DEFAULT_CHROMA_PORT = int(os.getenv("RAG_CHROMA_PORT", "8000"))
DEFAULT_COLLECTION_NAME = "rag_evidence_chunks"


class RagVectorRepository:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        persist_path: str = DEFAULT_CHROMA_PATH,
        host: str | None = DEFAULT_CHROMA_HOST,
        port: int = DEFAULT_CHROMA_PORT,
        collection_name: str = DEFAULT_COLLECTION_NAME,
    ) -> None:
        self.embedding_service = embedding_service
        self.persist_path = persist_path
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.client = self.create_client()
        self.collection = self.get_collection()

    def create_client(self):
        if self.host:
            return chromadb.HttpClient(host=self.host, port=self.port)

        return chromadb.PersistentClient(path=self.persist_path)

    def get_collection(self) -> Collection:
        return self.client.get_or_create_collection(name=self.collection_name)

    def save_chunks(self, chunks: list[RagEvidenceChunkDTO], run_id: int) -> int:
        if not chunks:
            return 0

        self.collection.upsert(
            ids=[chunk.id for chunk in chunks],
            documents=[chunk.chunk_text for chunk in chunks],
            embeddings=self.embedding_service.embed_texts(
                [chunk.chunk_text for chunk in chunks]
            ),
            metadatas=[self.build_metadata(chunk, run_id) for chunk in chunks],
        )
        return len(chunks)

    def count(self) -> int:
        return self.collection.count()

    def search(self, query: str, limit: int = 5) -> dict:
        return self.collection.query(
            query_embeddings=[self.embedding_service.embed_text(query)],
            n_results=limit,
        )

    def build_metadata(self, chunk: RagEvidenceChunkDTO, run_id: int) -> dict:
        return {
            "run_id": run_id,
            "path": chunk.path,
            "commit_sha": chunk.commit_sha,
            "language": chunk.language,
            "source_type": chunk.source_type,
            "chunk_type": chunk.chunk_type,
            "symbol_name": chunk.symbol_name or "",
            "start_line": chunk.start_line or 0,
            "end_line": chunk.end_line or 0,
            "citation": chunk.citation,
            "chunk_hash": chunk.chunk_hash,
            "chunk_index": chunk.chunk_index,
            "direct_implementation_evidence": (
                chunk.metadata.direct_implementation_evidence
            ),
        }
