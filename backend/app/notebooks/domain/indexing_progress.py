"""인덱싱 진행 레지스트리(스레드 안전 in-memory 싱글톤).

소스 인덱싱은 BackgroundTasks(스레드)에서 돌아가므로, 진행 상태를 여러
스레드가 안전하게 갱신/조회할 수 있어야 한다. source_id를 키로 단일 락 아래에서
스냅샷을 갱신한다. SSE/단발 조회는 to_view()로 깊은 복사된 dict를 받는다.
"""

import copy
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

ProgressStatus = Literal["queued", "running", "done", "failed"]
FileStatus = Literal["queued", "indexing", "done", "skipped", "failed"]


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class FileProgress:
    path: str
    language: str | None
    supported: bool
    status: FileStatus = "queued"
    chunks: int = 0

    def to_view(self) -> dict:
        return {
            "path": self.path,
            "language": self.language,
            "supported": self.supported,
            "status": self.status,
            "chunks": self.chunks,
        }


@dataclass(slots=True)
class IndexProgress:
    source_id: str
    notebook_id: str
    status: ProgressStatus = "queued"
    total_files: int = 0
    processed_files: int = 0
    skipped_files: int = 0
    total_chunks: int = 0
    indexed_chunks: int = 0
    error: str | None = None
    files: list[FileProgress] = field(default_factory=list)
    updated_at: datetime = field(default_factory=_utcnow)

    @property
    def percent(self) -> int:
        if self.status == "done":
            return 100
        if self.total_files <= 0:
            return 100 if self.status == "done" else 0
        ratio = self.processed_files / self.total_files
        return max(0, min(100, round(ratio * 100)))

    def to_view(self) -> dict:
        return {
            "source_id": self.source_id,
            "notebook_id": self.notebook_id,
            "status": self.status,
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "skipped_files": self.skipped_files,
            "total_chunks": self.total_chunks,
            "indexed_chunks": self.indexed_chunks,
            "percent": self.percent,
            "files": [file.to_view() for file in self.files],
            "error": self.error,
            "updated_at": self.updated_at.isoformat(),
        }


class IndexProgressRegistry:
    """source_id -> IndexProgress 매핑(락 보호)."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entries: dict[str, IndexProgress] = {}

    def register(self, source_id: str, notebook_id: str) -> None:
        with self._lock:
            self._entries[source_id] = IndexProgress(
                source_id=source_id,
                notebook_id=notebook_id,
                status="queued",
                updated_at=_utcnow(),
            )

    def get(self, source_id: str) -> dict | None:
        with self._lock:
            entry = self._entries.get(source_id)
            return entry.to_view() if entry is not None else None

    def remove(self, source_id: str) -> None:
        with self._lock:
            self._entries.pop(source_id, None)

    def update(self, source_id: str, mutate) -> None:
        """락 아래에서 진행 항목을 변형한다(mutate: Callable[[IndexProgress], None])."""
        with self._lock:
            entry = self._entries.get(source_id)
            if entry is None:
                return
            mutate(entry)
            entry.updated_at = _utcnow()

    def snapshot(self, source_id: str) -> IndexProgress | None:
        """현재 진행 상태의 깊은 복사본(락 밖에서 안전하게 읽기 위함)."""
        with self._lock:
            entry = self._entries.get(source_id)
            return copy.deepcopy(entry) if entry is not None else None


# 프로세스 단일 인스턴스(인덱싱 서비스/엔드포인트가 공유한다).
_REGISTRY = IndexProgressRegistry()


def get_progress_registry() -> IndexProgressRegistry:
    return _REGISTRY
