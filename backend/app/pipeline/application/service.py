from dataclasses import dataclass, field
from typing import Protocol

from app.pipeline.domain.agent import AgentProposalService
from app.pipeline.domain.approval import ApprovalService
from app.pipeline.domain.code_index import CodeIndexService
from app.pipeline.domain.publish import PublishService
from app.pipeline.domain.rag_index import RagIndexService
from app.pipeline.api.schemas import (
    AgentProposal,
    CodeReference,
    PipelineRequest,
    PipelineResponse,
    PublishSnapshot,
    RepoSnapshot,
    RetrievalChunk,
    StageResult,
)
from app.repository_source import RepoSyncService


class RepoSyncPort(Protocol):
    def sync(self, request: PipelineRequest) -> RepoSnapshot: ...


class CodeIndexPort(Protocol):
    def index(self, snapshot: RepoSnapshot) -> list[CodeReference]: ...


class RagIndexPort(Protocol):
    def index(
        self,
        snapshot: RepoSnapshot,
        references: list[CodeReference],
    ) -> list[RetrievalChunk]: ...


class AgentProposalPort(Protocol):
    def propose(
        self,
        references: list[CodeReference],
        chunks: list[RetrievalChunk],
    ) -> list[AgentProposal]: ...


class ApprovalPort(Protocol):
    def approve(self, proposals: list[AgentProposal]) -> list[AgentProposal]: ...


class PublishPort(Protocol):
    def publish(
        self,
        snapshot: RepoSnapshot,
        chunks: list[RetrievalChunk],
        proposals: list[AgentProposal],
    ) -> PublishSnapshot: ...


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
            stages=self._stage_results(artifacts),
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

    def _stage_results(self, artifacts: PipelineArtifacts) -> list[StageResult]:
        return [
            StageResult(id="repo-sync", status="done", detail=artifacts.repository.commit_sha),
            StageResult(id="code-index", status="done", detail=str(len(artifacts.code_references))),
            StageResult(id="rag-index", status="done", detail=str(len(artifacts.retrieval_chunks))),
            StageResult(
                id="agent-proposal",
                status="done",
                detail=str(len(artifacts.pending_proposals)),
            ),
            StageResult(id="approval", status="done", detail=str(len(artifacts.proposals))),
            StageResult(id="static-publish", status="done", detail=artifacts.publish_snapshot.path),
        ]
