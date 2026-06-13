from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

from app.pipeline.api.schemas import PipelineRequest, RepoFile
from app.repo_rag.api.schemas import RepoRagSyncRequest


def utcnow() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return str(uuid4())


def hash_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def file_hash(file: RepoFile) -> str:
    return hash_text(file.content)


def source_key(request: PipelineRequest) -> str:
    if request.repository_url:
        return request.repository_url.strip()
    return request.repository


def idempotency_key(request: RepoRagSyncRequest) -> str:
    requested_commit = request.requested_commit_sha or "latest"
    return ":".join(
        [
            source_key(request),
            request.branch,
            request.trigger_type,
            requested_commit,
        ]
    )


def lock_key(request: PipelineRequest) -> str:
    return f"{source_key(request)}:{request.branch}"
