"""NotebookStore의 Postgres 구현.

각 연산은 session_scope로 짧은 트랜잭션 경계를 잡는다. add/update는 PK 기준
merge(upsert)로 처리한다. 노트북 삭제 시 소속 소스를 함께 제거한다(앱 레벨
cascade — DB FK ON DELETE CASCADE와 동작을 맞춘다).
"""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.notebooks.domain.records import ChatMessageRecord, NotebookRecord, SourceRecord
from app.notebooks.infrastructure.mappers import (
    chat_message_to_model,
    chat_message_to_record,
    notebook_to_model,
    notebook_to_record,
    source_to_model,
    source_to_record,
)
from app.notebooks.infrastructure.models import ChatMessageModel, NotebookModel, SourceModel
from app.repo_rag.infrastructure.db import session_scope


class SqlNotebookStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # --- 노트북 ---

    def add_notebook(self, record: NotebookRecord) -> None:
        with session_scope(self._session_factory) as session:
            session.merge(notebook_to_model(record))

    def get_notebook(self, notebook_id: str) -> NotebookRecord:
        with session_scope(self._session_factory) as session:
            model = session.get(NotebookModel, notebook_id)
            if model is None:
                raise KeyError(notebook_id)
            return notebook_to_record(model)

    def list_notebooks(self) -> list[NotebookRecord]:
        with session_scope(self._session_factory) as session:
            stmt = select(NotebookModel).order_by(NotebookModel.created_at)
            return [notebook_to_record(model) for model in session.scalars(stmt).all()]

    def update_notebook(self, record: NotebookRecord) -> None:
        with session_scope(self._session_factory) as session:
            if session.get(NotebookModel, record.id) is None:
                raise KeyError(record.id)
            session.merge(notebook_to_model(record))

    def delete_notebook(self, notebook_id: str) -> None:
        with session_scope(self._session_factory) as session:
            model = session.get(NotebookModel, notebook_id)
            if model is None:
                raise KeyError(notebook_id)
            session.execute(
                delete(SourceModel).where(SourceModel.notebook_id == notebook_id)
            )
            session.execute(
                delete(ChatMessageModel).where(ChatMessageModel.notebook_id == notebook_id)
            )
            session.delete(model)

    # --- 소스 ---

    def add_source(self, record: SourceRecord) -> None:
        with session_scope(self._session_factory) as session:
            session.merge(source_to_model(record))

    def list_sources(self, notebook_id: str) -> list[SourceRecord]:
        with session_scope(self._session_factory) as session:
            stmt = (
                select(SourceModel)
                .where(SourceModel.notebook_id == notebook_id)
                .order_by(SourceModel.created_at)
            )
            return [source_to_record(model) for model in session.scalars(stmt).all()]

    def get_source(self, notebook_id: str, source_id: str) -> SourceRecord:
        with session_scope(self._session_factory) as session:
            model = session.get(SourceModel, source_id)
            if model is None or model.notebook_id != notebook_id:
                raise KeyError(source_id)
            return source_to_record(model)

    def delete_source(self, notebook_id: str, source_id: str) -> None:
        with session_scope(self._session_factory) as session:
            model = session.get(SourceModel, source_id)
            if model is None or model.notebook_id != notebook_id:
                raise KeyError(source_id)
            session.delete(model)

    # --- 채팅 메시지 ---

    def add_chat_message(self, record: ChatMessageRecord) -> None:
        with session_scope(self._session_factory) as session:
            session.merge(chat_message_to_model(record))

    def list_chat_messages(self, notebook_id: str) -> list[ChatMessageRecord]:
        with session_scope(self._session_factory) as session:
            if session.get(NotebookModel, notebook_id) is None:
                raise KeyError(notebook_id)
            stmt = (
                select(ChatMessageModel)
                .where(ChatMessageModel.notebook_id == notebook_id)
                .order_by(ChatMessageModel.created_at)
            )
            return [chat_message_to_record(model) for model in session.scalars(stmt).all()]

    def clear_chat_messages(self, notebook_id: str) -> None:
        with session_scope(self._session_factory) as session:
            if session.get(NotebookModel, notebook_id) is None:
                raise KeyError(notebook_id)
            stmt = delete(ChatMessageModel).where(ChatMessageModel.notebook_id == notebook_id)
            session.execute(stmt)
