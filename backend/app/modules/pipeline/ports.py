from typing import Protocol

from app.schemas import (
    AgentProposal,
    CodeReference,
    PipelineRequest,
    PublishSnapshot,
    RepoSnapshot,
    RetrievalChunk,
)


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
