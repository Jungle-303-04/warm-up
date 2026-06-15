import os

import chromadb
from chromadb.api.models.Collection import Collection

from app.rag.api.schema import RagEvidenceChunkDTO
from app.rag.external.embedding import EmbeddingService


DEFAULT_CHROMA_PATH = os.getenv("RAG_CHROMA_PATH", ".chroma/rag")
DEFAULT_CHROMA_HOST = os.getenv("RAG_CHROMA_HOST")
DEFAULT_CHROMA_PORT = int(os.getenv("RAG_CHROMA_PORT", "8000"))
DEFAULT_COLLECTION_NAME = "rag_evidence_chunks"


class RagVectorRepository:
    """RAG evidence chunk를 Chroma에 저장하고 의미 유사도 검색을 제공한다."""

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
        """환경 변수에 따라 Docker Chroma 서버 또는 로컬 persistent 저장소를 선택한다."""

        if self.host:
            return chromadb.HttpClient(host=self.host, port=self.port)

        return chromadb.PersistentClient(path=self.persist_path)

    def get_collection(self) -> Collection:
        """검색/저장 대상 collection이 없으면 생성해서 초기 실행을 단순하게 만든다."""

        return self.client.get_or_create_collection(name=self.collection_name)

    def save_chunks(
        self,
        chunks: list[RagEvidenceChunkDTO],
        run_id: int,
        repository_full_name: str | None = None,
        branch: str | None = None,
    ) -> int:
        """코드 기준 metadata를 붙여 청크를 벡터 DB에 upsert한다."""

        if not chunks:
            return 0

        self.collection.upsert(
            ids=[self.build_vector_id(run_id, chunk) for chunk in chunks],
            documents=[chunk.chunk_text for chunk in chunks],
            embeddings=self.embedding_service.embed_texts(
                [chunk.chunk_text for chunk in chunks]
            ),
            metadatas=[
                self.build_metadata(
                    chunk=chunk,
                    run_id=run_id,
                    repository_full_name=repository_full_name,
                    branch=branch,
                )
                for chunk in chunks
            ],
        )
        return len(chunks)

    def count(self) -> int:
        """시작 점검과 API 응답에서 collection 상태를 확인할 때 사용한다."""

        return self.collection.count()

    def search(
        self,
        query: str,
        limit: int = 5,
        run_id: int | None = None,
        repository_full_name: str | None = None,
        branch: str | None = None,
        commit_sha: str | None = None,
    ) -> dict:
        """질문을 embedding으로 바꾼 뒤 지정된 코드 기준 안에서 유사 청크를 찾는다."""

        query_arguments = {
            "query_embeddings": [self.embedding_service.embed_text(query)],
            "n_results": limit,
        }
        where_filter = build_where_filter(
            run_id=run_id,
            repository_full_name=repository_full_name,
            branch=branch,
            commit_sha=commit_sha,
        )
        if where_filter:
            query_arguments["where"] = where_filter

        return self.collection.query(**query_arguments)

    def build_metadata(
        self,
        chunk: RagEvidenceChunkDTO,
        run_id: int,
        repository_full_name: str | None,
        branch: str | None,
    ) -> dict:
        """검색 결과만으로도 레포, 커밋, citation을 추적할 수 있게 metadata를 만든다."""

        return {
            "run_id": run_id,
            "repository_full_name": repository_full_name or "",
            "branch": branch or "",
            "chunk_id": chunk.id,
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

    def build_vector_id(self, run_id: int, chunk: RagEvidenceChunkDTO) -> str:
        """같은 코드 조각이 여러 분석 run에 저장되어도 서로 덮어쓰지 않게 id를 만든다."""

        return f"{run_id}:{chunk.id}:{chunk.chunk_index}"


def build_where_filter(
    run_id: int | None = None,
    repository_full_name: str | None = None,
    branch: str | None = None,
    commit_sha: str | None = None,
) -> dict:
    """입력된 검색 기준만 Chroma metadata where 조건으로 바꾼다."""

    conditions = []

    if run_id is not None:
        conditions.append({"run_id": run_id})
    if repository_full_name:
        conditions.append({"repository_full_name": repository_full_name})
    if branch:
        conditions.append({"branch": branch})
    if commit_sha:
        conditions.append({"commit_sha": commit_sha})

    if not conditions:
        return {}

    if len(conditions) == 1:
        return conditions[0]

    return {"$and": conditions}
