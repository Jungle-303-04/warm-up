"""ChunkStore의 Postgres 구현.

검색은 pgvector 코사인 거리(의미)와 tsvector 키워드 점수를 각각 후보로 뽑아
가중 합산한 뒤 상위 청크를 돌려준다(SqlHybridRetriever와 동일한 패턴).
임베딩이 없으면 키워드만으로도 동작한다.
"""

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.notebooks.domain.chunk_records import ChunkSearchHit, NotebookChunk
from app.notebooks.infrastructure.mappers import chunk_to_model, chunk_to_record
from app.notebooks.infrastructure.models import NotebookChunkModel
from app.repo_rag.infrastructure.db import session_scope

VECTOR_WEIGHT = 0.7
KEYWORD_WEIGHT = 0.3
CANDIDATE_LIMIT = 50


class SqlChunkStore:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        *,
        text_config: str = "simple",
    ) -> None:
        self._session_factory = session_factory
        self._text_config = text_config

    def add_many(self, chunks: list[NotebookChunk]) -> None:
        if not chunks:
            return
        with session_scope(self._session_factory) as session:
            for chunk in chunks:
                session.merge(chunk_to_model(chunk))

    def delete_by_source(self, source_id: str) -> None:
        with session_scope(self._session_factory) as session:
            session.execute(
                delete(NotebookChunkModel).where(
                    NotebookChunkModel.source_id == source_id
                )
            )

    def count_by_source(self, source_id: str) -> int:
        with session_scope(self._session_factory) as session:
            return int(
                session.scalar(
                    select(func.count())
                    .select_from(NotebookChunkModel)
                    .where(NotebookChunkModel.source_id == source_id)
                )
                or 0
            )

    def search(
        self,
        notebook_id: str,
        *,
        query_embedding: list[float] | None,
        query_text: str,
        source_ids: list[str] | None,
        top_k: int,
    ) -> list[ChunkSearchHit]:
        with session_scope(self._session_factory) as session:
            vector_scores = (
                self._vector_candidates(session, notebook_id, source_ids, query_embedding)
                if query_embedding is not None
                else {}
            )
            keyword_scores = self._keyword_candidates(
                session, notebook_id, source_ids, query_text
            )

            fused: dict[str, float] = {}
            for chunk_id, score in vector_scores.items():
                fused[chunk_id] = fused.get(chunk_id, 0.0) + VECTOR_WEIGHT * score
            for chunk_id, score in keyword_scores.items():
                fused[chunk_id] = fused.get(chunk_id, 0.0) + KEYWORD_WEIGHT * score

            ranked = sorted(fused.items(), key=lambda item: item[1], reverse=True)[:top_k]
            if not ranked:
                return []

            ranked_ids = [chunk_id for chunk_id, _ in ranked]
            models = {
                model.id: model
                for model in session.scalars(
                    select(NotebookChunkModel).where(
                        NotebookChunkModel.id.in_(ranked_ids)
                    )
                ).all()
            }
            hits: list[ChunkSearchHit] = []
            for chunk_id, score in ranked:
                model = models.get(chunk_id)
                if model is None:
                    continue
                hits.append(ChunkSearchHit(chunk=chunk_to_record(model), score=float(score)))
            return hits

    def _scope(self, notebook_id: str, source_ids: list[str] | None) -> list:
        filters = [NotebookChunkModel.notebook_id == notebook_id]
        if source_ids is not None:
            filters.append(NotebookChunkModel.source_id.in_(source_ids))
        return filters

    def _vector_candidates(
        self,
        session: Session,
        notebook_id: str,
        source_ids: list[str] | None,
        query_embedding: list[float],
    ) -> dict[str, float]:
        distance = NotebookChunkModel.embedding.cosine_distance(query_embedding)
        rows = session.execute(
            select(NotebookChunkModel.id, distance.label("distance"))
            .where(
                *self._scope(notebook_id, source_ids),
                NotebookChunkModel.embedding.is_not(None),
            )
            .order_by(distance)
            .limit(CANDIDATE_LIMIT)
        ).all()
        return {row.id: 1.0 - float(row.distance) for row in rows}

    def _keyword_candidates(
        self,
        session: Session,
        notebook_id: str,
        source_ids: list[str] | None,
        query_text: str,
    ) -> dict[str, float]:
        if not query_text.strip():
            return {}
        ts_query = func.websearch_to_tsquery(self._text_config, query_text)
        rank = func.ts_rank_cd(NotebookChunkModel.content_tsv, ts_query)
        rows = session.execute(
            select(NotebookChunkModel.id, rank.label("rank"))
            .where(
                *self._scope(notebook_id, source_ids),
                NotebookChunkModel.content_tsv.op("@@")(ts_query),
            )
            .order_by(rank.desc())
            .limit(CANDIDATE_LIMIT)
        ).all()
        return {row.id: float(row.rank) for row in rows}
