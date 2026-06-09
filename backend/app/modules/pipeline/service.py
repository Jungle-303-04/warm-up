from dataclasses import dataclass, field

from app.modules.agent import AgentProposalService
from app.modules.approval import ApprovalService
from app.modules.code_index import CodeIndexService
from app.modules.pipeline.ports import (
    AgentProposalPort,
    ApprovalPort,
    CodeIndexPort,
    PublishPort,
    RagIndexPort,
    RepoSyncPort,
)
from app.modules.publish import PublishService
from app.modules.rag_index import RagIndexService
from app.modules.repo_sync import RepoSyncService
from app.pipeline import build_done_stage_results
from app.schemas import (
    AgentProposal,
    CodeReference,
    PipelineRequest,
    PipelineResponse,
    PublishSnapshot,
    RepoSnapshot,
    RetrievalChunk,
)


@dataclass(frozen=True)
class PipelineArtifacts:
    repository: RepoSnapshot
    code_references: list[CodeReference]
    retrieval_chunks: list[RetrievalChunk]
    pending_proposals: list[AgentProposal]
    proposals: list[AgentProposal]
    publish_snapshot: PublishSnapshot


@dataclass(slots=True)
class PipelineService:
    repo_sync: RepoSyncPort = field(default_factory=RepoSyncService)
    code_index: CodeIndexPort = field(default_factory=CodeIndexService)
    rag_index: RagIndexPort = field(default_factory=RagIndexService)
    agent: AgentProposalPort = field(default_factory=AgentProposalService)
    approval: ApprovalPort = field(default_factory=ApprovalService)
    publish: PublishPort = field(default_factory=PublishService)

    def run(self, request: PipelineRequest) -> PipelineResponse:
        artifacts = self._collect_artifacts(request)

        return PipelineResponse(
            repository=artifacts.repository,
            code_references=artifacts.code_references,
            retrieval_chunks=artifacts.retrieval_chunks,
            proposals=artifacts.proposals,
            publish_snapshot=artifacts.publish_snapshot,
            stages=build_done_stage_results(self._stage_details(artifacts)),
        )

    def _collect_artifacts(self, request: PipelineRequest) -> PipelineArtifacts:
        repository = self.repo_sync.sync(request)
        code_references = self.code_index.index(repository)
        retrieval_chunks = self.rag_index.index(repository, code_references)
        pending_proposals = self.agent.propose(code_references, retrieval_chunks)
        proposals = self.approval.approve(pending_proposals)
        publish_snapshot = self.publish.publish(repository, retrieval_chunks, proposals)

        return PipelineArtifacts(
            repository=repository,
            code_references=code_references,
            retrieval_chunks=retrieval_chunks,
            pending_proposals=pending_proposals,
            proposals=proposals,
            publish_snapshot=publish_snapshot,
        )

    def _stage_details(self, artifacts: PipelineArtifacts) -> dict[str, str]:
        return {
            "repo-sync": artifacts.repository.commit_sha,
            "code-index": str(len(artifacts.code_references)),
            "rag-index": str(len(artifacts.retrieval_chunks)),
            "agent-proposal": str(len(artifacts.pending_proposals)),
            "approval": str(len(artifacts.proposals)),
            "static-publish": artifacts.publish_snapshot.path,
        }
