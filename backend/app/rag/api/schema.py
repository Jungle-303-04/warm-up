from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.github.api.schema import GitHubFileResponseDTO, GitHubFileSnapshotDTO


MAX_SEARCH_LIMIT = 50


class RagChunkMetadataDTO(BaseModel):
    direct_implementation_evidence: bool


class RagEvidenceChunkDraftDTO(BaseModel):
    chunk_text: str
    chunk_type: str
    metadata: RagChunkMetadataDTO
    start_line: int | None = None
    end_line: int | None = None
    symbol_name: str | None = None

    @field_validator("chunk_text")
    @classmethod
    def validate_chunk_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("chunk text must not be empty")
        return value

    @field_validator("start_line", "end_line")
    @classmethod
    def validate_line(cls, value: int | None) -> int | None:
        if value is not None and value < 1:
            raise ValueError("line must be greater than or equal to 1")
        return value


class RagEvidenceChunkDTO(RagEvidenceChunkDraftDTO):
    id: str
    chunk_index: int
    chunk_hash: str
    path: str
    commit_sha: str
    language: str
    source_type: str
    citation: str


class GitHubRagPipelineRequestDTO(BaseModel):
    commit_sha: str
    files: list[GitHubFileResponseDTO]
    repository_full_name: str | None = None
    branch: str | None = None

    @field_validator("commit_sha")
    @classmethod
    def validate_commit_sha(cls, value: str) -> str:
        commit_sha = value.strip()
        if not commit_sha:
            raise ValueError("commit_sha must not be empty")
        return commit_sha

    @field_validator("files")
    @classmethod
    def validate_files(cls, value: list[GitHubFileResponseDTO]) -> list[GitHubFileResponseDTO]:
        if not value:
            raise ValueError("files must not be empty")
        return value


class GitHubRepositoryRefDTO(BaseModel):
    repository_full_name: str
    branch: str
    commit_sha: str


class GitHubRepositoryIndexRequestDTO(BaseModel):
    repository_full_name: str
    branch: str | None = None

    @field_validator("repository_full_name")
    @classmethod
    def validate_repository_full_name(cls, value: str) -> str:
        repository_full_name = normalize_repository_full_name(value)
        if "/" not in repository_full_name:
            raise ValueError("repository_full_name must use owner/repo format")
        owner, repo = repository_full_name.split("/", 1)
        if not owner.strip() or not repo.strip():
            raise ValueError("repository_full_name must use owner/repo format")
        return repository_full_name

    @field_validator("branch")
    @classmethod
    def validate_branch(cls, value: str | None) -> str | None:
        if value is None:
            return None
        branch = value.strip()
        return branch or None


def normalize_repository_full_name(value: str) -> str:
    repository = value.strip()
    if repository.startswith("git@github.com:"):
        repository = repository.replace("git@github.com:", "", 1)
    elif repository.startswith(("http://", "https://")):
        parsed = urlparse(repository)
        repository = parsed.path.strip("/")

    if repository.endswith(".git"):
        repository = repository[:-4]

    return repository.strip("/")


class GitHubRagSkippedFileDTO(BaseModel):
    path: str
    reason: str


class GitHubRagPipelineSummaryDTO(BaseModel):
    total_files: int
    indexed_files: int
    skipped_files: int
    total_chunks: int


class GitHubRagPipelineResultDTO(BaseModel):
    commit_sha: str
    file_snapshots: list[GitHubFileSnapshotDTO]
    evidence_chunks: list[RagEvidenceChunkDTO]
    skipped_files: list[GitHubRagSkippedFileDTO]
    summary: GitHubRagPipelineSummaryDTO


class RagStoredIndexResponseDTO(BaseModel):
    run_id: int
    reused: bool = False
    repository_full_name: str | None = None
    branch: str | None = None
    commit_sha: str
    vector_collection: str
    sql_chunk_count: int
    vector_chunk_count: int
    pipeline_result: GitHubRagPipelineResultDTO | None = None


class RagIndexRunDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repository_full_name: str | None = None
    branch: str | None = None
    commit_sha: str
    indexed_at: datetime
    total_files: int
    indexed_files: int
    skipped_files: int
    total_chunks: int


class RagFileSnapshotRecordDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    path: str
    name: str | None = None
    sha: str | None = None
    commit_sha: str
    language: str
    source_type: str
    content_hash: str
    citation: str
    size: int | None = None
    html_url: str | None = None


class RagChunkRecordDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    file_snapshot_id: int
    external_chunk_id: str
    chunk_hash: str
    chunk_index: int
    path: str
    commit_sha: str
    language: str
    source_type: str
    chunk_type: str
    symbol_name: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    citation: str
    chunk_text: str
    metadata_json: dict
    direct_implementation_evidence: bool


class RagSkippedFileRecordDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    path: str
    reason: str


class RagIndexRunListResponseDTO(BaseModel):
    items: list[RagIndexRunDTO]
    total: int


class RagIndexRunDetailDTO(BaseModel):
    run: RagIndexRunDTO
    file_snapshots: list[RagFileSnapshotRecordDTO]
    chunks: list[RagChunkRecordDTO]
    skipped_files: list[RagSkippedFileRecordDTO]


class RagSqlChunkSearchResponseDTO(BaseModel):
    keyword: str
    limit: int
    items: list[RagChunkRecordDTO]


class RagVectorSearchRequestDTO(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=MAX_SEARCH_LIMIT)
    run_id: int | None = Field(default=None, ge=1)
    repository_full_name: str | None = None
    branch: str | None = None
    commit_sha: str | None = None

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        query = value.strip()
        if not query:
            raise ValueError("query must not be empty")
        return query

    @field_validator("repository_full_name")
    @classmethod
    def validate_repository_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        repository_full_name = normalize_repository_full_name(value)
        if "/" not in repository_full_name:
            raise ValueError("repository_full_name must use owner/repo format")
        return repository_full_name

    @field_validator("branch", "commit_sha")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        return text or None


class RagVectorSearchItemDTO(BaseModel):
    id: str
    document: str
    metadata: dict
    distance: float | None = None


class RagVectorSearchResponseDTO(BaseModel):
    collection: str
    count: int
    query: str
    items: list[RagVectorSearchItemDTO]


class RagAskRequestDTO(BaseModel):
    question: str
    repository_full_name: str
    branch: str | None = None
    commit_sha: str | None = None
    limit: int = Field(default=5, ge=1, le=MAX_SEARCH_LIMIT)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        question = value.strip()
        if not question:
            raise ValueError("question must not be empty")
        return question

    @field_validator("repository_full_name")
    @classmethod
    def validate_repository_full_name(cls, value: str) -> str:
        repository_full_name = normalize_repository_full_name(value)
        if "/" not in repository_full_name:
            raise ValueError("repository_full_name must use owner/repo format")
        owner, repo = repository_full_name.split("/", 1)
        if not owner.strip() or not repo.strip():
            raise ValueError("repository_full_name must use owner/repo format")
        return repository_full_name

    @field_validator("branch", "commit_sha")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        return text or None


class RagAskSourceDTO(BaseModel):
    citation: str
    path: str
    chunk_type: str
    distance: float | None = None


class RagAskResponseDTO(BaseModel):
    answer: str
    repository_full_name: str | None = None
    branch: str | None = None
    commit_sha: str | None = None
    run_id: int | None = None
    sources: list[RagAskSourceDTO]
