from pathlib import PurePosixPath

from pydantic import BaseModel, field_validator


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


def validate_repository_path(value: str) -> str:
    path = value.strip()
    if not path:
        raise ValueError("file path must not be empty")

    parsed = PurePosixPath(path)
    if parsed.is_absolute() or ".." in parsed.parts:
        raise ValueError("file path must be a relative repository path")

    return path
