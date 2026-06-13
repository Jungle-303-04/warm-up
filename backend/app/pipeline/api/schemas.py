from pydantic import BaseModel, Field


DEFAULT_REPOSITORY = "sample-repo"
DEFAULT_BRANCH = "main"


class RepoFile(BaseModel):
    path: str
    content: str


def default_files() -> list[RepoFile]:
    return [
        RepoFile(
            path="backend/app/api/auth.py",
            content="def login(user_id: str) -> str:\n    return f'token:{user_id}'\n",
        ),
        RepoFile(
            path="docs/auth.md",
            content="# Auth\n\nLogin issues a token for the current user.\n",
        ),
    ]


class PipelineRequest(BaseModel):
    repository: str = DEFAULT_REPOSITORY
    branch: str = DEFAULT_BRANCH
    repository_path: str | None = None
    repository_url: str | None = None
    files: list[RepoFile] = Field(default_factory=default_files)


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


class RetrievalChunk(BaseModel):
    id: str
    source_path: str
    text: str
    citation: str


class AgentProposal(BaseModel):
    id: str
    type: str
    status: str
    target_path: str
    evidence: list[str]
    confidence: float
    proposed_change: str


class PublishSnapshot(BaseModel):
    id: str
    status: str
    path: str
    item_count: int
    proposal_count: int


class StageResult(BaseModel):
    id: str
    status: str
    detail: str


class PipelineStageResponse(BaseModel):
    id: str
    name: str
    purpose: str


class PipelineStagesResponse(BaseModel):
    stages: list[PipelineStageResponse]


class PipelineResponse(BaseModel):
    repository: RepoSnapshot
    code_references: list[CodeReference]
    retrieval_chunks: list[RetrievalChunk]
    proposals: list[AgentProposal]
    publish_snapshot: PublishSnapshot
    stages: list[StageResult]
