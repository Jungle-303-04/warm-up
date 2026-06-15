"""GitHub 웹훅 유스케이스.

push 이벤트를 파싱해 repo_rag 동기화 요청으로 변환하고 SyncTrigger로 시작한다.
서명 검증은 API 어댑터(라우터)가 담당하고, 여기서는 도메인 변환과 트리거만 한다.
"""

from dataclasses import dataclass

from app.github.domain.events import PushEvent, parse_push_event
from app.github.domain.ports import SyncTrigger
from app.repo_rag.api.schemas import RepoRagSyncRequest


@dataclass(slots=True)
class GitHubWebhookService:
    sync_trigger: SyncTrigger

    def handle_push(self, payload: dict) -> PushEvent:
        event = parse_push_event(payload)
        request = RepoRagSyncRequest(
            repository=event.repository_full_name,
            branch=event.branch,
            repository_url=event.repository_url,
            trigger_type="webhook",
            requested_commit_sha=event.commit_sha or None,
        )
        self.sync_trigger.trigger(request)
        return event
