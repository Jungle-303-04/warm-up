"""SQL-backed notebook indexing progress registry."""

import copy
from collections.abc import Callable

from sqlalchemy.orm import Session, sessionmaker

from app.notebooks.domain.indexing_progress import (
    FileProgress,
    IndexProgress,
    _utcnow,
)
from app.notebooks.infrastructure.models import NotebookIndexProgressModel
from app.repo_rag.infrastructure.db import session_scope


class SqlIndexProgressRegistry:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def register(self, source_id: str, notebook_id: str) -> None:
        with session_scope(self._session_factory) as session:
            previous = session.get(NotebookIndexProgressModel, source_id)
            progress = IndexProgress(
                source_id=source_id,
                notebook_id=notebook_id,
                status="queued",
                updated_at=_utcnow(),
                last_synced_at=previous.last_synced_at if previous is not None else None,
                content_hash=previous.content_hash if previous is not None else None,
            )
            session.merge(_to_model(progress))

    def get(self, source_id: str) -> dict | None:
        with session_scope(self._session_factory) as session:
            model = session.get(NotebookIndexProgressModel, source_id)
            return _to_progress(model).to_view() if model is not None else None

    def remove(self, source_id: str) -> None:
        with session_scope(self._session_factory) as session:
            model = session.get(NotebookIndexProgressModel, source_id)
            if model is not None:
                session.delete(model)

    def update(self, source_id: str, mutate: Callable[[IndexProgress], None]) -> None:
        with session_scope(self._session_factory) as session:
            model = session.get(NotebookIndexProgressModel, source_id)
            if model is None:
                return
            progress = _to_progress(model)
            mutate(progress)
            progress.updated_at = _utcnow()
            session.merge(_to_model(progress))

    def snapshot(self, source_id: str) -> IndexProgress | None:
        with session_scope(self._session_factory) as session:
            model = session.get(NotebookIndexProgressModel, source_id)
            if model is None:
                return None
            return copy.deepcopy(_to_progress(model))


def _to_model(progress: IndexProgress) -> NotebookIndexProgressModel:
    return NotebookIndexProgressModel(
        source_id=progress.source_id,
        notebook_id=progress.notebook_id,
        status=progress.status,
        total_files=progress.total_files,
        processed_files=progress.processed_files,
        skipped_files=progress.skipped_files,
        total_chunks=progress.total_chunks,
        indexed_chunks=progress.indexed_chunks,
        files=[file.to_view() for file in progress.files],
        error=progress.error,
        content_hash=progress.content_hash,
        updated_at=progress.updated_at,
        last_synced_at=progress.last_synced_at,
    )


def _to_progress(model: NotebookIndexProgressModel) -> IndexProgress:
    return IndexProgress(
        source_id=model.source_id,
        notebook_id=model.notebook_id,
        status=model.status,  # type: ignore[arg-type]
        total_files=model.total_files,
        processed_files=model.processed_files,
        skipped_files=model.skipped_files,
        total_chunks=model.total_chunks,
        indexed_chunks=model.indexed_chunks,
        files=[
            FileProgress(
                path=str(file.get("path") or ""),
                language=file.get("language"),
                supported=bool(file.get("supported")),
                status=file.get("status", "queued"),
                chunks=int(file.get("chunks") or 0),
            )
            for file in model.files
        ],
        error=model.error,
        updated_at=model.updated_at,
        last_synced_at=model.last_synced_at,
        content_hash=model.content_hash,
    )
