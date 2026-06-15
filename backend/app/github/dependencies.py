"""GitHub 연동 의존성 배선.

SyncTrigger 실제 구현은 repo_rag의 sync 서비스를 감싼다:
Postgres면 큐잉(enqueue), in-memory면 인라인 실행(run).
"""

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_claims, get_github_token_store
from app.auth.domain.records import SessionClaims
from app.auth.infrastructure.in_memory_token_store import InMemoryGitHubTokenStore
from app.config import Settings, get_settings
from app.github.application.webhook_service import GitHubWebhookService
from app.github.domain.ports import GitHubCommentClient
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


def get_comment_client(
    claims: SessionClaims = Depends(get_current_claims),
    token_store: InMemoryGitHubTokenStore = Depends(get_github_token_store),
) -> GitHubCommentClient:
    token = token_store.get(claims.user_id)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="연결된 GitHub 토큰이 없습니다. 다시 로그인하세요",
        )

    from app.github.infrastructure.http_client import HttpGitHubCommentClient

    return HttpGitHubCommentClient(token=token)
