from app.modules.agent import AgentProposalService
from app.modules.approval import ApprovalService
from app.modules.code_index import CodeIndexService
from app.modules.publish import PublishService
from app.modules.rag_index import RagIndexService
from app.modules.repo_sync import RepoSyncService
from app.schemas import PipelineRequest, PipelineResponse, StageResult


class PipelineService:
    def __init__(self) -> None:
        self.repo_sync = RepoSyncService()
        self.code_index = CodeIndexService()
        self.rag_index = RagIndexService()
        self.agent = AgentProposalService()
        self.approval = ApprovalService()
        self.publish = PublishService()

    def run(self, request: PipelineRequest) -> PipelineResponse:
        repository = self.repo_sync.sync(request)
        code_references = self.code_index.index(repository)
        retrieval_chunks = self.rag_index.index(repository, code_references)
        pending_proposals = self.agent.propose(code_references, retrieval_chunks)
        proposals = self.approval.approve(pending_proposals)
        publish_snapshot = self.publish.publish(repository, retrieval_chunks, proposals)

        return PipelineResponse(
            repository=repository,
            code_references=code_references,
            retrieval_chunks=retrieval_chunks,
            proposals=proposals,
            publish_snapshot=publish_snapshot,
            stages=[
                StageResult(id="repo-sync", status="done", detail=repository.commit_sha),
                StageResult(id="code-index", status="done", detail=str(len(code_references))),
                StageResult(id="rag-index", status="done", detail=str(len(retrieval_chunks))),
                StageResult(id="agent-proposal", status="done", detail=str(len(pending_proposals))),
                StageResult(id="approval", status="done", detail=str(len(proposals))),
                StageResult(id="static-publish", status="done", detail=publish_snapshot.path),
            ],
        )

