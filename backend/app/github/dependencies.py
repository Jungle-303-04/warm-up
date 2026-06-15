"""GitHub 연동 의존성 배선.

SyncTrigger 실제 구현은 repo_rag의 sync 서비스를 감싼다:
Postgres면 큐잉(enqueue), in-memory면 인라인 실행(run).
"""

from dataclasses import dataclass

from fastapi import Depends

from app.config import Settings, get_settings
from app.github.application.webhook_service import GitHubWebhookService
from app.repo_rag.api.schemas import RepoRagSyncRequest
from app.repo_rag.application.service import RepoRagSyncService
from app.repo_rag.dependencies import get_repo_rag_sync_service


@dataclass(slots=True)
class RepoRagSyncTrigger:
    service: RepoRagSyncService
    use_queue: bool

    def trigger(self, request: RepoRagSyncRequest) -> None:
        if self.use_queue:
            self.service.enqueue(request)
        else:
            self.service.run(request)


def get_webhook_service(
    settings: Settings = Depends(get_settings),
    sync_service: RepoRagSyncService = Depends(get_repo_rag_sync_service),
) -> GitHubWebhookService:
    trigger = RepoRagSyncTrigger(service=sync_service, use_queue=settings.uses_postgres)
    return GitHubWebhookService(sync_trigger=trigger)
