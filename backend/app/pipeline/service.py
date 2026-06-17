"""파이프라인 실행 유스케이스 서비스."""

from dataclasses import dataclass, field
from typing import Protocol

from app.pipeline.domain import (
    AGENT_PROPOSAL,
    APPROVAL,
    CODE_INDEX,
    DONE,
    RAG_INDEX,
    REPO_SYNC,
    AgentProposalService,
    ApprovalService,
    CodeIndexService,
    RagIndexService,
)
from app.pipeline.router import (
    AgentProposal,
    CodeReference,
    PipelineRequest,
    PipelineResponse,
    RepoSnapshot,
    RetrievalChunk,
    StageResult,
)
from app.repository_source.infrastructure.repo_sync import RepoSyncService


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


@dataclass(frozen=True)
class PipelineArtifacts:
    repository: RepoSnapshot
    code_references: list[CodeReference]
    retrieval_chunks: list[RetrievalChunk]
    pending_proposals: list[AgentProposal]
    proposals: list[AgentProposal]


@dataclass(slots=True)
class PipelineService:
    repo_sync: RepoSyncPort = field(default_factory=RepoSyncService)
    code_index: CodeIndexPort = field(default_factory=CodeIndexService)
    rag_index: RagIndexPort = field(default_factory=RagIndexService)
    agent: AgentProposalPort = field(default_factory=AgentProposalService)
    approval: ApprovalPort = field(default_factory=ApprovalService)

    def run(self, request: PipelineRequest) -> PipelineResponse:
        artifacts = self.collect(request)

        return PipelineResponse(
            repository=artifacts.repository,
            code_references=artifacts.code_references,
            retrieval_chunks=artifacts.retrieval_chunks,
            proposals=artifacts.proposals,
            stages=self._stage_results(artifacts),
        )

    def collect(self, request: PipelineRequest) -> PipelineArtifacts:
        """파이프라인을 끝까지 실행해 산출물(제안 포함)을 모은다."""
        repository = self.repo_sync.sync(request)
        code_references = self.code_index.index(repository)
        retrieval_chunks = self.rag_index.index(repository, code_references)
        pending_proposals = self.agent.propose(code_references, retrieval_chunks)
        proposals = self.approval.approve(pending_proposals)

        return PipelineArtifacts(
            repository=repository,
            code_references=code_references,
            retrieval_chunks=retrieval_chunks,
            pending_proposals=pending_proposals,
            proposals=proposals,
        )

    def _stage_results(self, artifacts: PipelineArtifacts) -> list[StageResult]:
        return [
            StageResult(
                id=REPO_SYNC,
                status=DONE,
                detail=artifacts.repository.commit_sha,
            ),
            StageResult(
                id=CODE_INDEX,
                status=DONE,
                detail=str(len(artifacts.code_references)),
            ),
            StageResult(
                id=RAG_INDEX,
                status=DONE,
                detail=str(len(artifacts.retrieval_chunks)),
            ),
            StageResult(
                id=AGENT_PROPOSAL,
                status=DONE,
                detail=str(len(artifacts.pending_proposals)),
            ),
            StageResult(
                id=APPROVAL,
                status=DONE,
                detail=str(len(artifacts.proposals)),
            ),
        ]
