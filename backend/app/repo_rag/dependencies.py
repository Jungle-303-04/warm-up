from functools import lru_cache

from app.repo_rag.in_memory_store import InMemoryRepoRagStore
from app.repo_rag.service import RepoRagSyncService
from app.repo_rag.store import RepoRagStore


@lru_cache(maxsize=1)
def get_repo_rag_store() -> RepoRagStore:
    return InMemoryRepoRagStore()


def get_repo_rag_sync_service() -> RepoRagSyncService:
    return RepoRagSyncService(store=get_repo_rag_store())
