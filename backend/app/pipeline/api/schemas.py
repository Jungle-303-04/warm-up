from pathlib import PurePosixPath

from pydantic import BaseModel, Field, field_validator

from app.pipeline.domain.constants import DEFAULT_BRANCH, DEFAULT_REPOSITORY, ProposalStatus, ProposalType


class RepoFile(BaseModel):
    path: str
    content: str

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        path = value.strip()
        if not path:
            raise ValueError("file path must not be empty")
        parsed = PurePosixPath(path)
        if parsed.is_absolute() or ".." in parsed.parts:
            raise ValueError("file path must be a relative repository path")
        return path


class PipelineRequest(BaseModel):
    repository: str = DEFAULT_REPOSITORY
    branch: str = DEFAULT_BRANCH
    repository_url: str | None = None
    files: list[RepoFile] = Field(default_factory=list)

    @field_validator("repository", "branch")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("value must not be empty")
        return text

    @field_validator("repository_url")
    @classmethod
    def validate_repository_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if not text:
            raise ValueError("repository_url must not be empty")
        return text


class RepoSnapshot(BaseModel):
    repository: str
    branch: str
    commit_sha: str
    files: list[RepoFile]


class CodeReference(BaseModel):
    id: str
    path: str
    symbol: str
    line: int
    commit_sha: str
    status: str

    @field_validator("line")
    @classmethod
    def validate_line(cls, value: int) -> int:
        if value < 1:
            raise ValueError("line must be greater than or equal to 1")
        return value


class RetrievalChunk(BaseModel):
    id: str
    source_path: str
    text: str
    citation: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("chunk text must not be empty")
        return value


class AgentProposal(BaseModel):
    id: str
    type: ProposalType
    status: ProposalStatus
    target_path: str
    evidence: list[str]
    confidence: float
    proposed_change: str

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, value: float) -> float:
        if not 0 <= value <= 1:
            raise ValueError("confidence must be between 0 and 1")
        return value


class StageResult(BaseModel):
    id: str
    status: str
    detail: str


class PipelineResponse(BaseModel):
    repository: RepoSnapshot
    code_references: list[CodeReference]
    retrieval_chunks: list[RetrievalChunk]
    proposals: list[AgentProposal]
    stages: list[StageResult]
