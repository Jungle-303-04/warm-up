"""노트북 의존성 배선.

POSTGRES_DATABASE_URL이 있으면 SQL 저장소(+pgvector 청크 검색)로, 없으면
in-memory로 동작한다. 임베딩은 기본 deterministic이라 외부 키 없이도
인덱싱·검색·채팅이 모두 동작한다. 저장소/레지스트리는 프로세스 단일
인스턴스(lru_cache)로 유지한다.
"""

from functools import lru_cache

from fastapi import Depends

from app.config import Settings, get_settings
from app.notebooks.domain.artifact_ports import ArtifactStore, LlmArtifactGenerator
from app.notebooks.domain.indexing_progress import (
    IndexProgressRegistry,
    get_progress_registry,
)
from app.notebooks.domain.ports import ChunkStore, NotebookStore
from app.notebooks.infrastructure.artifact_generators import (
    ChatOpenAIArtifactGenerator,
    DeterministicArtifactGenerator,
)
from app.notebooks.infrastructure.in_memory_artifact_store import InMemoryArtifactStore
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


def get_notebook_store(settings: Settings = Depends(get_settings)) -> NotebookStore:
    return _sql_store() if settings.uses_postgres else _in_memory_store()


def get_chunk_store(settings: Settings = Depends(get_settings)) -> ChunkStore:
    return _sql_chunk_store() if settings.uses_postgres else _in_memory_chunk_store()


def get_embedding_client(settings: Settings = Depends(get_settings)) -> EmbeddingClient:
    return build_embedding_client(settings)


def get_artifact_store(settings: Settings = Depends(get_settings)) -> ArtifactStore:
    return _sql_artifact_store() if settings.uses_postgres else _in_memory_artifact_store()


def _build_artifact_generator(settings: Settings) -> LlmArtifactGenerator:
    """산출물 생성기 선택.

    llm_provider="openai"이고 키가 있으면 LangChain ChatOpenAI 어댑터를, 아니면
    결정론 어댑터를 돌려준다. 결정론 어댑터는 키 없이도 dependency를 실제로 생성하고
    나머지 타입은 골격을 반환한다.
    """

    if settings.llm_provider == "openai" and settings.openai_api_key:
        from app.pipeline.infrastructure.chat_models import build_chat_model

        chat_model = build_chat_model(
            settings.llm_provider,
            settings.llm_model,
            settings.openai_api_key,
            temperature=0.0,
        )
        return ChatOpenAIArtifactGenerator(chat_model)
    return DeterministicArtifactGenerator()


def get_artifact_generator(
    settings: Settings = Depends(get_settings),
) -> LlmArtifactGenerator:
    return _build_artifact_generator(settings)


def get_progress_registry_dep() -> IndexProgressRegistry:
    return get_progress_registry()


def _build_llm_answerer(settings: Settings) -> "ChatAnswerer | None":
    """채팅 답변기 선택.

    llm_provider="openai"이고 키가 있으면 LangChain ChatOpenAI 답변기를 주입하고,
    아니면 None(결정론 폴백)을 돌려준다. _build_artifact_generator와 동일한 분기·
    빌드 패턴을 따른다(지연 import, 키/모델 주입).
    """

    if settings.llm_provider == "openai" and settings.openai_api_key:
        from app.notebooks.infrastructure.chat_answerers import (
            build_chat_openai_answerer,
        )

        return build_chat_openai_answerer(
            settings.llm_provider,
            settings.llm_model,
            settings.openai_api_key,
            temperature=0.0,
        )
    return None


def get_chat_answerer(
    settings: Settings = Depends(get_settings),
) -> "ChatAnswerer | None":
    return _build_llm_answerer(settings)
