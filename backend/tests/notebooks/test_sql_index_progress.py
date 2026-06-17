"""SQL indexing progress persistence integration tests.

These tests run only when POSTGRES_DATABASE_URL is configured. They prove that
the notebook indexing progress registry is not just an in-memory status holder:
a fresh registry instance can read the state written by a previous instance.
"""

import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest

POSTGRES_DATABASE_URL = os.getenv("POSTGRES_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_DATABASE_URL,
    reason="POSTGRES_DATABASE_URL이 설정된 경우에만 실행합니다",
)


def _session_factory():
    from sqlalchemy import text

    from app.notebooks.infrastructure.models import Base
    from app.repo_rag.infrastructure.db import create_db_engine, create_session_factory

    assert POSTGRES_DATABASE_URL is not None
    engine = create_db_engine(POSTGRES_DATABASE_URL)
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)
    return create_session_factory(engine)


def test_sql_index_progress_survives_registry_recreation() -> None:
    from app.notebooks.domain.indexing_progress import FileProgress
    from app.notebooks.infrastructure.models import NotebookModel, SourceModel
    from app.notebooks.infrastructure.sql_index_progress import SqlIndexProgressRegistry
    from app.repo_rag.infrastructure.db import session_scope

    session_factory = _session_factory()
    now = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    notebook_id = f"nb-{uuid4().hex}"
    source_id = f"src-{uuid4().hex}"

    with session_scope(session_factory) as session:
        session.add(
            NotebookModel(
                id=notebook_id,
                owner_user_id=1,
                title="progress persistence",
                created_at=now,
                updated_at=now,
            )
        )
        session.add(
            SourceModel(
                id=source_id,
                notebook_id=notebook_id,
                kind="md",
                title="progress.md",
                content="# progress",
                created_at=now,
            )
        )

    try:
        registry = SqlIndexProgressRegistry(session_factory)
        registry.register(source_id, notebook_id)

        def mark_done(progress):
            progress.status = "done"
            progress.total_files = 1
            progress.processed_files = 1
            progress.total_chunks = 2
            progress.indexed_chunks = 2
            progress.files = [
                FileProgress(
                    path="progress.md",
                    language="markdown",
                    supported=True,
                    status="done",
                    chunks=2,
                )
            ]
            progress.content_hash = "content-hash-v1"
            progress.last_synced_at = now

        registry.update(source_id, mark_done)

        restarted_registry = SqlIndexProgressRegistry(session_factory)
        persisted = restarted_registry.get(source_id)

        assert persisted is not None
        assert persisted["status"] == "done"
        assert persisted["indexed_chunks"] == 2
        assert persisted["content_hash"] == "content-hash-v1"
        assert persisted["last_synced_at"] == now.isoformat()
        assert persisted["files"] == [
            {
                "path": "progress.md",
                "language": "markdown",
                "supported": True,
                "status": "done",
                "chunks": 2,
            }
        ]

        # Re-registering for a reindex resets transient progress to queued while
        # preserving the last successful sync identity shown in the UI.
        restarted_registry.register(source_id, notebook_id)
        queued = SqlIndexProgressRegistry(session_factory).get(source_id)

        assert queued is not None
        assert queued["status"] == "queued"
        assert queued["last_synced_at"] == now.isoformat()
        assert queued["content_hash"] == "content-hash-v1"
    finally:
        with session_scope(session_factory) as session:
            notebook = session.get(NotebookModel, notebook_id)
            if notebook is not None:
                session.delete(notebook)
