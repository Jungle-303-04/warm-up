"""노트북 의존성 배선.

POSTGRES_DATABASE_URL이 있으면 SQL 저장소(+pgvector 청크 검색)로, 없으면
in-memory로 동작한다. 임베딩은 기본 deterministic이라 외부 키 없이도
인덱싱·검색·채팅이 모두 동작한다. 저장소/레지스트리는 프로세스 단일
인스턴스(lru_cache)로 유지한다.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from fastapi import Depends

from app.auth.dependencies import get_github_token_store
from app.auth.domain.ports import GitHubTokenStore
from app.config import Settings, get_settings
from app.link_metadata.dependencies import get_link_fetcher
from app.link_metadata.domain.ports import LinkFetcher
from app.notebooks.assembly.components import (
    build_answer_planner,
    build_artifact_generator,
    build_chat_answerer,
    build_commit_history_fetcher,
)
from app.notebooks.domain.artifact_ports import ArtifactStore, LlmArtifactGenerator
from app.notebooks.domain.indexing_progress import (
    IndexProgressRegistry,
    get_progress_registry,
)
from app.notebooks.domain.ports import ChunkStore, IndexingProgressStore, NotebookStore
from app.notebooks.infrastructure.in_memory_artifact_store import InMemoryArtifactStore
from app.notebooks.infrastructure.in_memory_chunk_store import InMemoryChunkStore
from app.notebooks.infrastructure.in_memory_store import InMemoryNotebookStore
from app.repo_rag.dependencies import build_embedding_client
from app.repo_rag.domain.ports import EmbeddingClient

if TYPE_CHECKING:
    from app.notebooks.application.answer_planner import AnswerPlanner
    from app.notebooks.application.artifact_service import ArtifactService
    from app.notebooks.application.chat_service import (
        ChatAnswerer,
        ChatService,
        CommitHistoryFetcher,
    )
    from app.notebooks.application.indexing_service import IndexingService
    from app.notebooks.application.service import NotebookService


@lru_cache(maxsize=1)
def _in_memory_store() -> InMemoryNotebookStore:
    return InMemoryNotebookStore()


@lru_cache(maxsize=1)
def _in_memory_chunk_store() -> InMemoryChunkStore:
    return InMemoryChunkStore()


@lru_cache(maxsize=1)
def _in_memory_artifact_store() -> InMemoryArtifactStore:
    return InMemoryArtifactStore()


@lru_cache(maxsize=1)
def _sql_artifact_store() -> ArtifactStore:
    settings = get_settings()
    if settings.postgres_database_url is None:
        raise RuntimeError("POSTGRES_DATABASE_URL is required for SQL storage")

    from app.notebooks.infrastructure.sql_artifact_store import SqlArtifactStore
    from app.repo_rag.infrastructure.db import get_shared_session_factory

    session_factory = get_shared_session_factory(settings.postgres_database_url)
    return SqlArtifactStore(session_factory)


@lru_cache(maxsize=1)
def _sql_store() -> NotebookStore:
    settings = get_settings()
    if settings.postgres_database_url is None:
        raise RuntimeError("POSTGRES_DATABASE_URL is required for SQL storage")

    from app.notebooks.infrastructure.sql_store import SqlNotebookStore
    from app.repo_rag.infrastructure.db import get_shared_session_factory

    session_factory = get_shared_session_factory(settings.postgres_database_url)
    return SqlNotebookStore(session_factory)


@lru_cache(maxsize=1)
def _sql_chunk_store() -> ChunkStore:
    settings = get_settings()
    if settings.postgres_database_url is None:
        raise RuntimeError("POSTGRES_DATABASE_URL is required for SQL storage")

    from app.notebooks.infrastructure.sql_chunk_store import SqlChunkStore
    from app.repo_rag.infrastructure.db import get_shared_session_factory

    session_factory = get_shared_session_factory(settings.postgres_database_url)
    return SqlChunkStore(session_factory, text_config=settings.search_text_config)


@lru_cache(maxsize=1)
def _sql_progress_registry() -> IndexingProgressStore:
    settings = get_settings()
    if settings.postgres_database_url is None:
        raise RuntimeError("POSTGRES_DATABASE_URL is required for SQL indexing progress")

    from app.notebooks.infrastructure.sql_index_progress import SqlIndexProgressRegistry
    from app.repo_rag.infrastructure.db import get_shared_session_factory

    session_factory = get_shared_session_factory(settings.postgres_database_url)
    return SqlIndexProgressRegistry(session_factory)


def get_notebook_store(settings: Settings = Depends(get_settings)) -> NotebookStore:
    return _sql_store() if settings.uses_postgres else _in_memory_store()


def get_chunk_store(settings: Settings = Depends(get_settings)) -> ChunkStore:
    return _sql_chunk_store() if settings.uses_postgres else _in_memory_chunk_store()


def get_embedding_client(settings: Settings = Depends(get_settings)) -> EmbeddingClient:
    return build_embedding_client(settings)


def get_artifact_store(settings: Settings = Depends(get_settings)) -> ArtifactStore:
    return _sql_artifact_store() if settings.uses_postgres else _in_memory_artifact_store()


def get_artifact_generator(
    settings: Settings = Depends(get_settings),
) -> LlmArtifactGenerator:
    return build_artifact_generator(settings)


def get_progress_registry_dep(
    settings: Settings = Depends(get_settings),
) -> IndexingProgressStore:
    return _sql_progress_registry() if settings.uses_postgres else get_progress_registry()


def get_chat_answerer(
    settings: Settings = Depends(get_settings),
) -> ChatAnswerer | None:
    return build_chat_answerer(settings)


def get_commit_history_fetcher(
    token_store: GitHubTokenStore = Depends(get_github_token_store),
) -> CommitHistoryFetcher:
    return build_commit_history_fetcher(token_store)


def get_answer_planner(
    settings: Settings = Depends(get_settings),
) -> AnswerPlanner:
    return build_answer_planner(settings)


def _clock():
    from app.notebooks.application.service import get_clock

    return get_clock()


def _id_factory():
    from app.notebooks.application.service import get_id_factory

    return get_id_factory()


def get_notebook_service(
    store: NotebookStore = Depends(get_notebook_store),
    clock=Depends(_clock),
    id_factory=Depends(_id_factory),
) -> NotebookService:
    from app.notebooks.application.service import NotebookService

    return NotebookService(store=store, clock=clock, id_factory=id_factory)


def get_chat_service(
    store: NotebookStore = Depends(get_notebook_store),
    chunk_store: ChunkStore = Depends(get_chunk_store),
    embedder: EmbeddingClient = Depends(get_embedding_client),
    answerer: ChatAnswerer | None = Depends(get_chat_answerer),
    commit_fetcher: CommitHistoryFetcher = Depends(get_commit_history_fetcher),
    answer_planner: AnswerPlanner = Depends(get_answer_planner),
    settings: Settings = Depends(get_settings),
    clock=Depends(_clock),
    id_factory=Depends(_id_factory),
) -> ChatService:
    from app.notebooks.application.chat_service import ChatService

    return ChatService(
        store=store,
        chunk_store=chunk_store,
        embedder=embedder,
        answerer=answerer,
        settings=settings,
        clock=clock,
        id_factory=id_factory,
        commit_fetcher=commit_fetcher,
        answer_planner=answer_planner,
    )


def get_indexing_service(
    store: NotebookStore = Depends(get_notebook_store),
    chunk_store: ChunkStore = Depends(get_chunk_store),
    embedder: EmbeddingClient = Depends(get_embedding_client),
    registry: IndexProgressRegistry = Depends(get_progress_registry_dep),
    url_fetcher: LinkFetcher = Depends(get_link_fetcher),
    clock=Depends(_clock),
    id_factory=Depends(_id_factory),
) -> IndexingService:
    from app.notebooks.application.indexing_service import IndexingService

    return IndexingService(
        store=store,
        chunk_store=chunk_store,
        embedder=embedder,
        registry=registry,
        url_fetcher=url_fetcher,
        clock=clock,
        id_factory=id_factory,
    )


def get_artifact_service(
    store: NotebookStore = Depends(get_notebook_store),
    artifact_store: ArtifactStore = Depends(get_artifact_store),
    generator: LlmArtifactGenerator = Depends(get_artifact_generator),
    settings: Settings = Depends(get_settings),
    clock=Depends(_clock),
    id_factory=Depends(_id_factory),
) -> ArtifactService:
    from app.notebooks.application.artifact_service import ArtifactService

    return ArtifactService(
        store=store,
        artifact_store=artifact_store,
        generator=generator,
        settings=settings,
        clock=clock,
        id_factory=id_factory,
    )
