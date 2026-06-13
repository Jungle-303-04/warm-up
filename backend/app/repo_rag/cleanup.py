from dataclasses import dataclass
from datetime import datetime

from app.repo_rag.store import RepoRagStore


@dataclass(slots=True)
class RetentionCleanupService:
    store: RepoRagStore

    def cleanup(self, *, batch_size: int, cutoff: datetime) -> int:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero")
        return self.store.hard_delete_inactive(batch_size=batch_size, cutoff=cutoff)
