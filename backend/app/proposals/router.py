"""제안 리뷰 API 라우터 및 스키마 정의."""

from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict

from app.api.responses import BAD_REQUEST_RESPONSE
from app.auth.dependencies import get_current_claims
from app.pipeline.router import PipelineRequest, ProposalStatus, ProposalType
from app.proposals.domain import ProposalRecord
from app.proposals.service import ProposalReviewService

router = APIRouter(dependencies=[Depends(get_current_claims)])


# --- API 스키마 DTO 정의 ---
class GenerateProposalsRequest(PipelineRequest):
    """제안 생성 요청. 파이프라인 입력을 재사용."""
    pass


class ProposalDecisionRequest(BaseModel):
    reason: str | None = None


class ProposalView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    repository: str
    target_path: str
    type: ProposalType
    proposed_change: str
    evidence: list[str]
    confidence: float
    status: ProposalStatus
    created_at: datetime
    decided_at: datetime | None = None
    decided_reason: str | None = None


class ProposalListResponse(BaseModel):
    proposals: list[ProposalView]


# --- API 엔드포인트 라우팅 정의 ---
@router.post(
    "/proposals",
    response_model=ProposalListResponse,
    status_code=status.HTTP_201_CREATED,
    responses=BAD_REQUEST_RESPONSE,
)
def generate_proposals(
    request: GenerateProposalsRequest,
    service: ProposalReviewService = Depends(ProposalReviewService),
) -> ProposalListResponse:
    records = service.generate(request)
    return ProposalListResponse(proposals=records)


@router.get("/proposals", response_model=ProposalListResponse)
def list_proposals(
    repository: str | None = Query(default=None),
    status_filter: ProposalStatus | None = Query(default=None, alias="status"),
    service: ProposalReviewService = Depends(ProposalReviewService),
) -> ProposalListResponse:
    records = service.list(repository=repository, status=status_filter)
    return ProposalListResponse(proposals=records)


@router.get(
    "/proposals/{proposal_id}",
    response_model=ProposalView,
    responses=BAD_REQUEST_RESPONSE,
)
def get_proposal(
    proposal_id: str,
    service: ProposalReviewService = Depends(ProposalReviewService),
) -> ProposalRecord:
    return service.get(proposal_id)


@router.post(
    "/proposals/{proposal_id}/approve",
    response_model=ProposalView,
    responses=BAD_REQUEST_RESPONSE,
)
def approve_proposal(
    proposal_id: str,
    body: ProposalDecisionRequest,
    service: ProposalReviewService = Depends(ProposalReviewService),
) -> ProposalRecord:
    return service.approve(proposal_id, body.reason)


@router.post(
    "/proposals/{proposal_id}/reject",
    response_model=ProposalView,
    responses=BAD_REQUEST_RESPONSE,
)
def reject_proposal(
    proposal_id: str,
    body: ProposalDecisionRequest,
    service: ProposalReviewService = Depends(ProposalReviewService),
) -> ProposalRecord:
    return service.reject(proposal_id, body.reason)
