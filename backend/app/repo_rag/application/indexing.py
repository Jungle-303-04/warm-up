"""인덱싱 유스케이스: 변경 파일을 청킹하고 임베딩을 부착한다.

임베딩 생성 책임을 저장소(store)에서 분리해 이 서비스가 담당한다.
embedder가 없으면 임베딩 없이(None) 청크만 만든다(in-memory 경로/테스트용).
"""

from dataclasses import dataclass, field

from app.pipeline.router import RepoSnapshot
from app.repo_rag.api.schemas import RepoFileChange
from app.repo_rag.domain.chunking import ChunkingService
from app.repo_rag.domain.ports import EmbeddingClient
from app.repo_rag.domain.records import EmbeddedChunk


@dataclass(slots=True)
class IndexingService:
    chunking: ChunkingService = field(default_factory=ChunkingService)
    embedder: EmbeddingClient | None = None

    def index_changes(
        self,
        snapshot: RepoSnapshot,
        changes: list[RepoFileChange],
    ) -> list[EmbeddedChunk]:
        chunks = self.chunking.chunk_changed_files(snapshot, changes)
        if not chunks:
            return []

        if self.embedder is None:
            return [EmbeddedChunk(chunk=chunk) for chunk in chunks]

        vectors = self.embedder.embed_documents([chunk.text for chunk in chunks])
        return [
            EmbeddedChunk(chunk=chunk, embedding=vector)
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
