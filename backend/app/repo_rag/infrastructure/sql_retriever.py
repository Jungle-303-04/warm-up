"""Postgres 하이브리드 리트리버.

키워드(tsvector + ts_rank_cd)와 벡터(pgvector 코사인) 후보를 각각 뽑아
도메인의 fuse_scores 로 가중합한 뒤 상위 결과를 돌려준다.
sqlalchemy/pgvector에 의존하므로 Postgres 경로에서만 import 한다.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.repo_rag.domain.ports import EmbeddingClient
from app.repo_rag.domain.retrieval import SearchHit, fuse_scores, rank_fused
from app.repo_rag.infrastructure.mappers import to_chunk_record
from app.repo_rag.infrastructure.models import ChunkModel, active_filters


class SqlHybridRetriever:
    """RepoRagRetriever 포트의 Postgres 구현 (요청 단위 Session 주입)."""

    def __init__(
        self,
        session: Session,
        embedding_client: EmbeddingClient,
        *,
        vector_weight: float,
        keyword_weight: float,
        text_config: str,
        candidate_limit: int,
    ) -> None:
        self._db = session
        self._embedding_client = embedding_client
        self._vector_weight = vector_weight
        self._keyword_weight = keyword_weight
        self._text_config = text_config
        self._candidate_limit = candidate_limit

    def search(self, repository_id: str, query: str, limit: int = 10) -> list[SearchHit]:
        query_embedding = self._embedding_client.embed_query(query)
        session = self._db

        vector_scores = self._vector_candidates(session, repository_id, query_embedding)
        keyword_scores = self._keyword_candidates(session, repository_id, query)

        fused = fuse_scores(
            vector_scores=vector_scores,
            keyword_scores=keyword_scores,
            vector_weight=self._vector_weight,
            keyword_weight=self._keyword_weight,
        )
        ranked = rank_fused(fused, limit)
        if not ranked:
            return []

        ranked_ids = [candidate_id for candidate_id, _ in ranked]
        chunk_models = {
            model.id: model
            for model in session.scalars(
                select(ChunkModel).where(ChunkModel.id.in_(ranked_ids))
            ).all()
        }

        hits: list[SearchHit] = []
        for candidate_id, score in ranked:
            model = chunk_models.get(candidate_id)
            if model is None:
                continue
            hits.append(
                SearchHit(
                    chunk=to_chunk_record(model).to_chunk(),
                    score=score.final,
                    vector_score=score.vector_score,
                    keyword_score=score.keyword_score,
                )
            )
        return hits

    def _vector_candidates(
        self,
        session: Session,
        repository_id: str,
        query_embedding: list[float],
    ) -> dict[str, float]:
        distance = ChunkModel.embedding.cosine_distance(query_embedding)
        rows = session.execute(
            select(ChunkModel.id, distance.label("distance"))
            .where(
                ChunkModel.repository_id == repository_id,
                *active_filters(ChunkModel),
                ChunkModel.embedding.is_not(None),
            )
            .order_by(distance)
            .limit(self._candidate_limit)
        ).all()
        return {row.id: 1.0 - float(row.distance) for row in rows}

    def _keyword_candidates(
        self,
        session: Session,
        repository_id: str,
        query: str,
    ) -> dict[str, float]:
        ts_query = func.websearch_to_tsquery(self._text_config, query)
        rank = func.ts_rank_cd(ChunkModel.content_tsv, ts_query)
        rows = session.execute(
            select(ChunkModel.id, rank.label("rank"))
            .where(
                ChunkModel.repository_id == repository_id,
                *active_filters(ChunkModel),
                ChunkModel.content_tsv.op("@@")(ts_query),
            )
            .order_by(rank.desc())
            .limit(self._candidate_limit)
        ).all()
        return {row.id: float(row.rank) for row in rows}
