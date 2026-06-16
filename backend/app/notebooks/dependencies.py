"""노트북 의존성 배선.

POSTGRES_DATABASE_URL이 있으면 SQL 저장소(+pgvector 청크 검색)로, 없으면
in-memory로 동작한다. 임베딩은 기본 deterministic이라 외부 키 없이도
인덱싱·검색·채팅이 모두 동작한다. 저장소/레지스트리는 프로세스 단일
인스턴스(lru_cache)로 유지한다.
"""

from functools import lru_cache

from fastapi import Depends

from app.config import Settings, get_settings
from app.notebooks.application.chat_service import ChatAnswerer, ChatService, TextChunk
from app.notebooks.application.indexing_service import IndexingService
from app.notebooks.application.service import NotebookService
from app.notebooks.domain.indexing_progress import (
    IndexProgressRegistry,
    get_progress_registry,
)
from app.notebooks.domain.ports import ChunkStore, NotebookStore
from app.notebooks.infrastructure.in_memory_chunk_store import InMemoryChunkStore
from app.notebooks.infrastructure.in_memory_store import InMemoryNotebookStore
from app.repo_rag.dependencies import build_embedding_client
from app.repo_rag.domain.ports import EmbeddingClient


@lru_cache(maxsize=1)
def _in_memory_store() -> InMemoryNotebookStore:
    return InMemoryNotebookStore()


@lru_cache(maxsize=1)
def _in_memory_chunk_store() -> InMemoryChunkStore:
    return InMemoryChunkStore()


@lru_cache(maxsize=1)
def _sql_store() -> NotebookStore:
    settings = get_settings()
    if settings.postgres_database_url is None:
        raise RuntimeError("POSTGRES_DATABASE_URL is required for SQL storage")

    from app.notebooks.infrastructure.sql_store import SqlNotebookStore
    from app.repo_rag.infrastructure.db import create_db_engine, create_session_factory

    session_factory = create_session_factory(create_db_engine(settings.postgres_database_url))
    return SqlNotebookStore(session_factory)


@lru_cache(maxsize=1)
def _sql_chunk_store() -> ChunkStore:
    settings = get_settings()
    if settings.postgres_database_url is None:
        raise RuntimeError("POSTGRES_DATABASE_URL is required for SQL storage")

    from app.notebooks.infrastructure.sql_chunk_store import SqlChunkStore
    from app.repo_rag.infrastructure.db import create_db_engine, create_session_factory

    session_factory = create_session_factory(create_db_engine(settings.postgres_database_url))
    return SqlChunkStore(session_factory, text_config=settings.search_text_config)


def get_notebook_store(settings: Settings = Depends(get_settings)) -> NotebookStore:
    return _sql_store() if settings.uses_postgres else _in_memory_store()


def get_chunk_store(settings: Settings = Depends(get_settings)) -> ChunkStore:
    return _sql_chunk_store() if settings.uses_postgres else _in_memory_chunk_store()


def get_embedding_client(settings: Settings = Depends(get_settings)) -> EmbeddingClient:
    return build_embedding_client(settings)


def get_progress_registry_dep() -> IndexProgressRegistry:
    return get_progress_registry()


def get_notebook_service(
    store: NotebookStore = Depends(get_notebook_store),
) -> NotebookService:
    return NotebookService(store=store)


def get_indexing_service(
    store: NotebookStore = Depends(get_notebook_store),
    chunk_store: ChunkStore = Depends(get_chunk_store),
    embedder: EmbeddingClient = Depends(get_embedding_client),
    registry: IndexProgressRegistry = Depends(get_progress_registry_dep),
) -> IndexingService:
    # repo 재풀링(reindex 최신화)을 위해 RepoSyncService를 주입한다.
    from app.repository_source.infrastructure.repo_sync import RepoSyncService

    return IndexingService(
        store=store,
        chunk_store=chunk_store,
        embedder=embedder,
        registry=registry,
        repo_sync=RepoSyncService(),
    )


def _build_llm_answerer(settings: Settings) -> ChatAnswerer | None:
    if settings.llm_provider == "none" or not settings.openai_api_key:
        return None

    if settings.llm_provider != "openai":
        return None

    from app.pipeline.infrastructure.chat_models import build_chat_model

    model = build_chat_model(
        settings.llm_provider,
        settings.llm_model,
        settings.openai_api_key,
        temperature=0.0,
    )

    def answer(question: str, evidence: list[TextChunk]) -> str:
        context = "\n\n".join(
            f"[{index}] {chunk.path or chunk.source_title}\n{chunk.text}"
            for index, chunk in enumerate(evidence, start=1)
        )
        response = model.invoke(
            "다음 근거만 사용해 한국어로 간결하게 답하세요. "
            "근거에 없는 내용은 추측하지 마세요.\n\n"
            f"질문: {question}\n\n근거:\n{context}"
        )
        content = getattr(response, "content", response)
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "\n".join(str(part) for part in content)
        return str(content)

    return answer


def get_notebook_chat_service(
    store: NotebookStore = Depends(get_notebook_store),
    chunk_store: ChunkStore = Depends(get_chunk_store),
    embedder: EmbeddingClient = Depends(get_embedding_client),
    settings: Settings = Depends(get_settings),
) -> ChatService:
    return ChatService(
        store=store,
        chunk_store=chunk_store,
        embedder=embedder,
        answerer=_build_llm_answerer(settings),
    )
