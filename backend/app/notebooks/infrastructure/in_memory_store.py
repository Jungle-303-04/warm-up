"""NotebookStore의 in-memory 구현(개발/테스트/단일 프로세스용).

노트북 삭제 시 소속 소스를 cascade로 함께 제거한다.
"""

from app.notebooks.domain.ports import NotebookStore
from app.notebooks.domain.records import ChatMessageRecord, NotebookRecord, SourceRecord
from app.api.errors import EntityNotFoundError


class InMemoryNotebookStore(NotebookStore):

    def __init__(self) -> None:
        self._notebooks: dict[str, NotebookRecord] = {}
        self._sources: dict[str, SourceRecord] = {}
        self._chat_messages: dict[str, ChatMessageRecord] = {}

    # --- 노트북 ---

    def add_notebook(self, record: NotebookRecord) -> None:
        self._notebooks[record.id] = record

    def get_notebook(self, notebook_id: str) -> NotebookRecord:
        if notebook_id not in self._notebooks:
            raise EntityNotFoundError(notebook_id)
        return self._notebooks[notebook_id]

    def list_notebooks(self) -> list[NotebookRecord]:
        return list(self._notebooks.values())

    def update_notebook(self, record: NotebookRecord) -> None:
        if record.id not in self._notebooks:
            raise EntityNotFoundError(record.id)
        self._notebooks[record.id] = record

    def delete_notebook(self, notebook_id: str) -> None:
        if notebook_id not in self._notebooks:
            raise EntityNotFoundError(notebook_id)
        del self._notebooks[notebook_id]
        # cascade: 소속 소스 제거
        for source_id in [
            sid
            for sid, source in self._sources.items()
            if source.notebook_id == notebook_id
        ]:
            del self._sources[source_id]
        for message_id in [
            mid
            for mid, message in self._chat_messages.items()
            if message.notebook_id == notebook_id
        ]:
            del self._chat_messages[message_id]

    # --- 소스 ---

    def add_source(self, record: SourceRecord) -> None:
        self._sources[record.id] = record

    def list_sources(self, notebook_id: str) -> list[SourceRecord]:
        items = [
            source
            for source in self._sources.values()
            if source.notebook_id == notebook_id
        ]
        return sorted(items, key=lambda source: source.created_at)

    def get_source(self, notebook_id: str, source_id: str) -> SourceRecord:
        source = self._sources.get(source_id)
        if source is None or source.notebook_id != notebook_id:
            raise EntityNotFoundError(source_id)
        return source

    def delete_source(self, notebook_id: str, source_id: str) -> None:
        source = self._sources.get(source_id)
        if source is None or source.notebook_id != notebook_id:
            raise EntityNotFoundError(source_id)
        del self._sources[source_id]

    # --- 채팅 메시지 ---

    def add_chat_message(self, record: ChatMessageRecord) -> None:
        self._chat_messages[record.id] = record

    def list_chat_messages(self, notebook_id: str) -> list[ChatMessageRecord]:
        self.get_notebook(notebook_id)
        items = [
            message
            for message in self._chat_messages.values()
            if message.notebook_id == notebook_id
        ]
        return sorted(items, key=lambda message: message.created_at)

    def clear_chat_messages(self, notebook_id: str) -> None:
        self.get_notebook(notebook_id)
        to_delete = [
            mid
            for mid, message in self._chat_messages.items()
            if message.notebook_id == notebook_id
        ]
        for mid in to_delete:
            del self._chat_messages[mid]
