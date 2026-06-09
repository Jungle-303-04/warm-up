from dataclasses import dataclass, field
from typing import Protocol

from app.pipeline import build_done_stage_results
from app.schemas.pipeline import (
    AgentProposal,
    CodeReference,
    PipelineRequest,
    PipelineResponse,
    PublishSnapshot,
    RepoSnapshot,
    RetrievalChunk,
)
from app.services.agent import AgentProposalService
from app.services.approval import ApprovalService
from app.services.code_index import CodeIndexService
from app.services.publish import PublishService
from app.services.rag_index import RagIndexService
from app.services.repo_sync import RepoSyncService


# Protocol은 상속 강제가 아니라 "이 메서드를 가진 객체면 된다"는 구조적 인터페이스다.
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
    # 각 stage의 중간 산출물을 하나로 묶어 response 생성과 stage detail 생성을 분리한다.
    repository: RepoSnapshot
    code_references: list[CodeReference]
    retrieval_chunks: list[RetrievalChunk]
    pending_proposals: list[AgentProposal]
    proposals: list[AgentProposal]
    publish_snapshot: PublishSnapshot


@dataclass(slots=True)
class PipelineService:
    # 각 stage 구현체를 주입받게 두면 테스트 fake나 실제 GitHub/RAG 구현으로 쉽게 교체할 수 있다.
    repo_sync: RepoSyncPort = field(default_factory=RepoSyncService)
    code_index: CodeIndexPort = field(default_factory=CodeIndexService)
    rag_index: RagIndexPort = field(default_factory=RagIndexService)
    agent: AgentProposalPort = field(default_factory=AgentProposalService)
    approval: ApprovalPort = field(default_factory=ApprovalService)
    publish: PublishPort = field(default_factory=PublishService)

    def run(self, request: PipelineRequest) -> PipelineResponse:
        # route가 호출하는 public use case entrypoint다.
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
        # 최소 파이프라인은 sync -> index -> retrieve -> propose -> approve -> publish 순서로 흐른다.
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
