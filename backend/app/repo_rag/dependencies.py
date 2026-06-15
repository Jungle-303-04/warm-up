"""FastAPI 네이티브 의존성 배선.

- 트랜잭션 경계: 서비스가 `with uow_factory() as uow:`로 잡는다(유스케이스 단위).
- DI: 별도 컨테이너 없이 모듈 팩토리 함수 + Depends 체인으로 조립.
- POSTGRES_DATABASE_URL이 없으면 in-memory UoW로 동작.
"""

from functools import lru_cache

from fastapi import Depends, HTTPException, status

from app.config import Settings, get_settings
from app.repo_rag.application.service import RepoRagSyncService
from app.repo_rag.application.types import UowFactory
from app.repo_rag.application.unit_of_work import InMemoryUnitOfWork
from app.repo_rag.domain.ports import EmbeddingClient


@lru_cache(maxsize=1)
def _session_factory():
    settings = get_settings()
    from app.repo_rag.infrastructure.db import create_db_engine, create_session_factory

    if settings.postgres_database_url is None:
        raise RuntimeError("POSTGRES_DATABASE_URL is required for SQL storage")
    return create_session_factory(create_db_engine(settings.postgres_database_url))


@lru_cache(maxsize=1)
def _in_memory_store():
    from app.repo_rag.infrastructure.in_memory_store import InMemoryRepoRagStore

    return InMemoryRepoRagStore()


def get_uow_factory(
    settings: Settings = Depends(get_settings),
) -> UowFactory:
    if settings.uses_postgres:
        from app.repo_rag.infrastructure.sql_unit_of_work import SqlUnitOfWork

        session_factory = _session_factory()
        return lambda: SqlUnitOfWork(session_factory)

    store = _in_memory_store()
    return lambda: InMemoryUnitOfWork(_repo_rag=store)


def build_embedding_client(settings: Settings) -> EmbeddingClient:
    if settings.embedding_provider == "openai":
        from app.repo_rag.infrastructure.embeddings import OpenAIEmbeddingClient

        return OpenAIEmbeddingClient(
            model=settings.embedding_model,
            dimension=settings.embedding_dimension,
            api_key=settings.openai_api_key,
        )

    from app.repo_rag.infrastructure.embeddings import DeterministicEmbeddingClient

    return DeterministicEmbeddingClient(dimension=settings.embedding_dimension)


def get_embedder(
    settings: Settings = Depends(get_settings),
) -> EmbeddingClient | None:
    if not settings.uses_postgres:
        return None
    return build_embedding_client(settings)


def get_repo_rag_sync_service(
    uow_factory: UowFactory = Depends(get_uow_factory),
    embedder: EmbeddingClient | None = Depends(get_embedder),
) -> RepoRagSyncService:
    return RepoRagSyncService(uow_factory=uow_factory, embedder=embedder)


def get_repo_rag_search_service(
    settings: Settings = Depends(get_settings),
    uow_factory: UowFactory = Depends(get_uow_factory),
    embedder: EmbeddingClient | None = Depends(get_embedder),
):
    if not settings.uses_postgres or embedder is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="하이브리드 검색은 Postgres 저장소에서만 지원됩니다",
        )

    from app.repo_rag.application.search_service import RepoRagSearchService
    from app.repo_rag.infrastructure.sql_retriever import SqlHybridRetriever

    def retriever_factory(session):
        return SqlHybridRetriever(
            session,
            embedder,
            vector_weight=settings.hybrid_vector_weight,
            keyword_weight=settings.hybrid_keyword_weight,
            text_config=settings.search_text_config,
            candidate_limit=settings.search_candidate_limit,
        )

    return RepoRagSearchService(uow_factory=uow_factory, retriever_factory=retriever_factory)
