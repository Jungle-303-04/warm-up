"""인메모리 기반 노트북, 아티팩트 및 청크 저장소 구현."""

import math
import re
import threading

from app.api.errors import EntityNotFoundError
from app.notebooks.domain import (
    ArtifactRecord,
    ChatMessageRecord,
    ChunkSearchHit,
    NotebookChunk,
    NotebookRecord,
    SourceRecord,
)
from app.notebooks.ports import ArtifactStore, ChunkStore, NotebookStore

_TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣_./-]+")


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


class InMemoryArtifactStore(ArtifactStore):
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._artifacts: dict[str, ArtifactRecord] = {}

    def add(self, record: ArtifactRecord) -> None:
        with self._lock:
            self._artifacts[record.id] = record

    def get(self, notebook_id: str, artifact_id: str) -> ArtifactRecord:
        with self._lock:
            record = self._artifacts.get(artifact_id)
            if record is None or record.notebook_id != notebook_id:
                raise EntityNotFoundError(artifact_id)
            return record

    def list_by_notebook(self, notebook_id: str) -> list[ArtifactRecord]:
        with self._lock:
            items = [
                record
                for record in self._artifacts.values()
                if record.notebook_id == notebook_id
            ]
        # created_at 오름차순(None은 뒤로).
        return sorted(
            items,
            key=lambda record: (record.created_at is None, record.created_at),
        )

    def update(self, record: ArtifactRecord) -> None:
        with self._lock:
            existing = self._artifacts.get(record.id)
            if existing is None or existing.notebook_id != record.notebook_id:
                raise EntityNotFoundError(record.id)
            self._artifacts[record.id] = record

    def delete(self, notebook_id: str, artifact_id: str) -> None:
        with self._lock:
            record = self._artifacts.get(artifact_id)
            if record is None or record.notebook_id != notebook_id:
                raise EntityNotFoundError(artifact_id)
            del self._artifacts[artifact_id]


class InMemoryChunkStore(ChunkStore):
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._chunks: dict[str, NotebookChunk] = {}

    def add_many(self, chunks: list[NotebookChunk]) -> None:
        with self._lock:
            for chunk in chunks:
                self._chunks[chunk.id] = chunk

    def delete_by_source(self, source_id: str) -> None:
        with self._lock:
            for chunk_id in [
                cid
                for cid, chunk in self._chunks.items()
                if chunk.source_id == source_id
            ]:
                del self._chunks[chunk_id]

    def count_by_source(self, source_id: str) -> int:
        with self._lock:
            return sum(
                1 for chunk in self._chunks.values() if chunk.source_id == source_id
            )

    def search(
        self,
        notebook_id: str,
        *,
        query_embedding: list[float] | None,
        query_text: str,
        source_ids: list[str] | None,
        top_k: int,
        file_paths: list[str] | None = None,
    ) -> list[ChunkSearchHit]:
        # file_paths가 주어지면 파일 단위 범위 필터: file_path가 없는(비repo 본문)
        # 청크는 항상 통과시키고, 경로가 있는(repo 파일) 청크는 선택된 경로만 후보로 둔다.
        allowed_paths = set(file_paths) if file_paths is not None else None
        with self._lock:
            candidates = [
                chunk
                for chunk in self._chunks.values()
                if chunk.notebook_id == notebook_id
                and (source_ids is None or chunk.source_id in source_ids)
                and (
                    allowed_paths is None
                    or chunk.file_path is None
                    or chunk.file_path in allowed_paths
                )
            ]

        query_tokens = _tokens(query_text)
        scored: list[tuple[float, int, ChunkSearchHit]] = []
        for index, chunk in enumerate(candidates):
            score = 0.0
            if query_embedding is not None and chunk.embedding is not None:
                score = _cosine(query_embedding, chunk.embedding)
            matched = _matched_terms(query_tokens, chunk)
            if score <= 0.0 and matched:
                # 임베딩이 없거나 의미 점수가 0이면 키워드 부분일치로 폴백.
                score = 0.001 * len(matched)
            if score <= 0.0:
                continue
            hit = ChunkSearchHit(chunk=chunk, score=score, matched_terms=matched)
            scored.append((score, index, hit))

        scored.sort(key=lambda item: (-item[0], item[1]))
        return [hit for _, _, hit in scored[:top_k]]


def _cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        return 0.0
    dot = 0.0
    left_norm = 0.0
    right_norm = 0.0
    for a, b in zip(left, right, strict=False):
        dot += a * b
        left_norm += a * a
        right_norm += b * b
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (math.sqrt(left_norm) * math.sqrt(right_norm))


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in _TOKEN_RE.findall(text)
        if len(token.strip("._/-")) >= 2
    }


def _matched_terms(query_tokens: set[str], chunk: NotebookChunk) -> list[str]:
    if not query_tokens:
        return []
    haystack = f"{chunk.file_path or ''} {chunk.text}".lower()
    return sorted(token for token in query_tokens if token in haystack)
