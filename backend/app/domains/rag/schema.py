from pydantic import BaseModel, field_validator

from app.domains.github.schema import GitHubFileResponseDTO, GitHubFileSnapshotDTO


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
