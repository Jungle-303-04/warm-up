"""ArtifactStore의 in-memory 구현(개발/테스트/단일 프로세스용).

get/update/delete는 notebook_id가 일치하지 않으면 KeyError를 던진다(API에서 404).
목록은 created_at 오름차순(없으면 입력 순서)으로 돌려준다.
"""

import threading

from app.notebooks.domain.artifact_records import ArtifactRecord


class InMemoryArtifactStore:
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
                raise KeyError(artifact_id)
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
                raise KeyError(record.id)
            self._artifacts[record.id] = record

    def delete(self, notebook_id: str, artifact_id: str) -> None:
        with self._lock:
            record = self._artifacts.get(artifact_id)
            if record is None or record.notebook_id != notebook_id:
                raise KeyError(artifact_id)
            del self._artifacts[artifact_id]
