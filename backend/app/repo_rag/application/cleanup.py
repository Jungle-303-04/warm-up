from dataclasses import dataclass
from datetime import datetime

from app.repo_rag.infrastructure.store import RepoRagStore
from app.validation import min_value


@dataclass(slots=True)
class RetentionCleanupService:
    store: RepoRagStore

    def cleanup(self, *, batch_size: int, cutoff: datetime) -> int:
        min_value(batch_size, 1, "batch_size는 1 이상이어야 합니다")
        return self.store.hard_delete_inactive(batch_size=batch_size, cutoff=cutoff)
