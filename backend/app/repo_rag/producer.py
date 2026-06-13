from dataclasses import dataclass

from app.repo_rag.records import SyncJobRecord
from app.repo_rag.schemas import RepoRagSyncRequest, SyncTriggerType
from app.repo_rag.store import RepoRagStore
from app.pipeline.schemas import PipelineRequest


@dataclass(slots=True)
class SyncJobProducer:
    store: RepoRagStore

    def enqueue(self, request: RepoRagSyncRequest) -> SyncJobRecord:
        return self.store.create_job(request)

    def enqueue_manual(self, request: PipelineRequest) -> SyncJobRecord:
        return self.enqueue(_repo_rag_request(request, trigger_type="manual"))

    def enqueue_schedule(self, request: PipelineRequest) -> SyncJobRecord:
        return self.enqueue(_repo_rag_request(request, trigger_type="schedule"))

    def enqueue_webhook(
        self,
        request: PipelineRequest,
        requested_commit_sha: str,
    ) -> SyncJobRecord:
        return self.enqueue(
            _repo_rag_request(
                request,
                trigger_type="webhook",
                requested_commit_sha=requested_commit_sha,
            )
        )


def _repo_rag_request(
    request: PipelineRequest,
    *,
    trigger_type: SyncTriggerType,
    requested_commit_sha: str | None = None,
) -> RepoRagSyncRequest:
    payload = request.model_dump()
    payload["trigger_type"] = trigger_type
    payload["requested_commit_sha"] = requested_commit_sha
    return RepoRagSyncRequest.model_validate(payload)
