from fastapi import APIRouter, Depends, Query, status

from app.api.errors import http_error
from app.api.responses import BAD_REQUEST_RESPONSE
from app.auth.dependencies import get_current_claims
from app.pipeline.api.schemas import ProposalStatus
from app.proposals.api.schemas import (
    GenerateProposalsRequest,
    ProposalDecisionRequest,
    ProposalListResponse,
    ProposalView,
)
from app.proposals.application.service import ProposalReviewService
from app.proposals.domain.records import ProposalRecord

router = APIRouter(dependencies=[Depends(get_current_claims)])

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

