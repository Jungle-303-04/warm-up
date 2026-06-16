"""노트북 의존성 배선.

POSTGRES_DATABASE_URL이 있으면 SQL 저장소로 영속화하고, 없으면 in-memory로
동작한다. 저장소는 프로세스 단일 인스턴스로 유지(lru_cache)한다.
"""

from functools import lru_cache

from fastapi import Depends

from app.config import Settings, get_settings
from app.notebooks.application.service import NotebookService
from app.notebooks.domain.ports import NotebookStore
from app.notebooks.infrastructure.in_memory_store import InMemoryNotebookStore


@lru_cache(maxsize=1)
def _in_memory_store() -> InMemoryNotebookStore:
    return InMemoryNotebookStore()


@lru_cache(maxsize=1)
def _sql_store() -> NotebookStore:
    settings = get_settings()
    if settings.postgres_database_url is None:
        raise RuntimeError("POSTGRES_DATABASE_URL is required for SQL storage")

    from app.notebooks.infrastructure.sql_store import SqlNotebookStore
    from app.repo_rag.infrastructure.db import create_db_engine, create_session_factory

    session_factory = create_session_factory(create_db_engine(settings.postgres_database_url))
    return SqlNotebookStore(session_factory)


def get_notebook_store(settings: Settings = Depends(get_settings)) -> NotebookStore:
    return _sql_store() if settings.uses_postgres else _in_memory_store()


def get_notebook_service(
    store: NotebookStore = Depends(get_notebook_store),
) -> NotebookService:
    return NotebookService(store=store)
