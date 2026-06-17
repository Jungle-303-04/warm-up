"""RAG 분석 파이프라인 API 라우터 및 스키마 DTO 정의."""

from enum import StrEnum
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, field_validator
from typing import Any

from app.api.errors import http_error
from app.api.responses import BAD_REQUEST_RESPONSE
from app.auth.dependencies import get_current_claims
from app.validation import between, min_value, relative_path, required_text


# --- 1. 파이프라인 API 스키마 DTO 정의 (schemas.py) ---
DEFAULT_REPO = "sample-repo"
DEFAULT_BRANCH = "main"


class ProposalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ProposalType(StrEnum):
    RELATED_CODE = "related_code_suggestion"


class RepoFile(BaseModel):
    path: str
    content: str

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return relative_path(
            value,
            empty_message="파일 경로는 비어 있을 수 없습니다",
            invalid_message="파일 경로는 저장소 기준 상대 경로여야 합니다",
        )


class PipelineRequest(BaseModel):
    repository: str = DEFAULT_REPO
    branch: str = DEFAULT_BRANCH
    repository_url: str | None = None
    files: list[RepoFile] = Field(default_factory=list)

    @field_validator("repository", "branch")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return required_text(value, "값은 비어 있을 수 없습니다")

    @field_validator("repository_url")
    @classmethod
    def validate_repository_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return required_text(value, "repository_url은 비어 있을 수 없습니다")


class RepoSnapshot(BaseModel):
    repository: str
    branch: str
    commit_sha: str
    files: list[RepoFile]


class CodeReference(BaseModel):
    id: str
    path: str
    symbol: str
    kind: str = "symbol"
    line: int
    commit_sha: str
    status: str

    @field_validator("line")
    @classmethod
    def validate_line(cls, value: int) -> int:
        return min_value(value, 1, "line은 1 이상이어야 합니다")


class RetrievalChunk(BaseModel):
    id: str
    source_path: str
    text: str
    citation: str
    chunk_type: str | None = None
    symbol_name: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    language: str | None = None

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return required_text(value, "청크 텍스트는 비어 있을 수 없습니다")


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
        return between(value, 0, 1, "confidence는 0 이상 1 이하이어야 합니다")


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


# --- 2. API 엔드포인트 라우팅 정의 (router.py) ---
# 지연 임포트로 의존성 꼬임 방지
def get_pipeline_service_instance():
    from app.pipeline.dependencies import get_pipeline_service
    return get_pipeline_service()


router = APIRouter(dependencies=[Depends(get_current_claims)])


@router.post(
    "/run",
    response_model=PipelineResponse,
    status_code=status.HTTP_200_OK,
    responses=BAD_REQUEST_RESPONSE,
)
def run_pipeline(
    request: PipelineRequest,
    service: Any = Depends(get_pipeline_service_instance),
) -> PipelineResponse:
    from app.pipeline.service import PipelineService
    return http_error(
        lambda: service.run(request),
        {ValueError: status.HTTP_400_BAD_REQUEST},
    )
