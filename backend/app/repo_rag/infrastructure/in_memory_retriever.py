import math
import re

from app.repo_rag.domain.ports import EmbeddingClient
from app.repo_rag.domain.retrieval import SearchHit, fuse_scores, rank_fused
from app.repo_rag.infrastructure.in_memory_store import InMemoryRepoRagStore

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9가-힣_]+")


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in _TOKEN_PATTERN.findall(text) if token}


def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    if len(v1) != len(v2) or not v1 or not v2:
        return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2, strict=False))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


class InMemoryHybridRetriever:
    """InMemoryRepoRagStore와 DeterministicEmbeddingClient 기반의 인메모리 하이브리드 리트리버."""

    def __init__(
        self,
        store: InMemoryRepoRagStore,
        embedding_client: EmbeddingClient,
        *,
        vector_weight: float = 0.5,
        keyword_weight: float = 0.5,
        candidate_limit: int = 50,
    ) -> None:
        self._store = store
        self._embedding_client = embedding_client
        self._vector_weight = vector_weight
        self._keyword_weight = keyword_weight
        self._candidate_limit = candidate_limit

    def search(self, repository_id: str, query: str, limit: int = 10) -> list[SearchHit]:
        # active chunks 가져오기
        active_retrieval_chunks = self._store.active_chunks(repository_id)
        if not active_retrieval_chunks:
            return []

        # 1. 벡터 코사인 유사도 계산
        query_embedding = self._embedding_client.embed_query(query)
        vector_scores: dict[str, float] = {}
        for chunk in active_retrieval_chunks:
            chunk_embedding = self._store.embeddings.get(chunk.id)
            if chunk_embedding:
                similarity = _cosine_similarity(query_embedding, chunk_embedding)
                vector_scores[chunk.id] = similarity
            else:
                vector_scores[chunk.id] = 0.0

        # 2. 키워드 매칭 스코어 계산 (단어 매칭 개수 기반 유사도)
        query_tokens = _tokenize(query)
        keyword_scores: dict[str, float] = {}
        for chunk in active_retrieval_chunks:
            chunk_tokens = _tokenize(chunk.text)
            if not query_tokens or not chunk_tokens:
                keyword_scores[chunk.id] = 0.0
                continue
            
            # 교집합 크기를 매칭 점수로 산출
            intersection = query_tokens.intersection(chunk_tokens)
            keyword_scores[chunk.id] = len(intersection) / len(query_tokens)

        # 3. 점수 융합 및 정렬
        fused = fuse_scores(
            vector_scores=vector_scores,
            keyword_scores=keyword_scores,
            vector_weight=self._vector_weight,
            keyword_weight=self._keyword_weight,
        )
        ranked = rank_fused(fused, limit)
        if not ranked:
            return []

        # 4. SearchHit 매핑
        chunk_map = {chunk.id: chunk for chunk in active_retrieval_chunks}
        hits: list[SearchHit] = []
        for candidate_id, score in ranked:
            chunk = chunk_map.get(candidate_id)
            if chunk is None:
                continue
            hits.append(
                SearchHit(
                    chunk=chunk,
                    score=score.final,
                    vector_score=score.vector_score,
                    keyword_score=score.keyword_score,
                )
            )
        return hits
