# GitHub API 응답과 RAG용 파일 snapshot DTO를 정의하는 파일
# repository path 검증도 여기서 같이 처리
from pathlib import PurePosixPath

from pydantic import BaseModel, field_validator


# GitHub file content response DTO
class GitHubFileResponseDTO(BaseModel):
    path: str
    content: str
    name: str | None = None
    sha: str | None = None
    encoding: str = "utf-8"
    size: int | None = None
    html_url: str | None = None

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return validate_repository_path(value)


# RAG pipeline에서 사용할 GitHub file snapshot DTO
class GitHubFileSnapshotDTO(BaseModel):
    path: str
    commit_sha: str
    language: str
    source_type: str
    content_text: str
    content_hash: str
    citation: str
    name: str | None = None
    sha: str | None = None
    size: int | None = None
    html_url: str | None = None

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return validate_repository_path(value)


# repository 내부 상대 경로인지 검증
def validate_repository_path(value: str) -> str:
    path = value.strip()
    if not path:
        raise ValueError("file path must not be empty")

    parsed = PurePosixPath(path)
    if parsed.is_absolute() or ".." in parsed.parts:
        raise ValueError("file path must be a relative repository path")

    return path
