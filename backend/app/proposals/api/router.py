from fastapi import APIRouter, Depends, Query, status

from app.api.errors import http_error
from app.api.responses import BAD_REQUEST_RESPONSE
from app.pipeline.api.schemas import ProposalStatus
from app.proposals.api.schemas import (
    GenerateProposalsRequest,
    ProposalDecisionRequest,
    ProposalListResponse,
    ProposalView,
)
from app.proposals.application.service import ProposalReviewService
from app.proposals.dependencies import get_proposal_review_service

router = APIRouter()

NOT_FOUND = {KeyError: status.HTTP_404_NOT_FOUND}
NOT_FOUND_OR_CONFLICT = {KeyError: status.HTTP_404_NOT_FOUND, ValueError: status.HTTP_409_CONFLICT}


@router.post(
    "/proposals",
    response_model=ProposalListResponse,
    status_code=status.HTTP_201_CREATED,
    responses=BAD_REQUEST_RESPONSE,
)
def generate_proposals(
    request: GenerateProposalsRequest,
    service: ProposalReviewService = Depends(get_proposal_review_service),
) -> ProposalListResponse:
    def run() -> ProposalListResponse:
        records = service.generate(request)
        return ProposalListResponse(proposals=[ProposalView.from_record(r) for r in records])

    return http_error(run, {ValueError: status.HTTP_400_BAD_REQUEST})


@router.get("/proposals", response_model=ProposalListResponse)
def list_proposals(
    repository: str | None = Query(default=None),
    status_filter: ProposalStatus | None = Query(default=None, alias="status"),
    service: ProposalReviewService = Depends(get_proposal_review_service),
) -> ProposalListResponse:
    records = service.list(repository=repository, status=status_filter)
    return ProposalListResponse(proposals=[ProposalView.from_record(r) for r in records])


@router.get(
    "/proposals/{proposal_id}",
    response_model=ProposalView,
    responses=BAD_REQUEST_RESPONSE,
)
def get_proposal(
    proposal_id: str,
    service: ProposalReviewService = Depends(get_proposal_review_service),
) -> ProposalView:
    return http_error(lambda: ProposalView.from_record(service.get(proposal_id)), NOT_FOUND)


@router.post(
    "/proposals/{proposal_id}/approve",
    response_model=ProposalView,
    responses=BAD_REQUEST_RESPONSE,
)
def approve_proposal(
    proposal_id: str,
    body: ProposalDecisionRequest,
    service: ProposalReviewService = Depends(get_proposal_review_service),
) -> ProposalView:
    return http_error(
        lambda: ProposalView.from_record(service.approve(proposal_id, body.reason)),
        NOT_FOUND_OR_CONFLICT,
    )


@router.post(
    "/proposals/{proposal_id}/reject",
    response_model=ProposalView,
    responses=BAD_REQUEST_RESPONSE,
)
def reject_proposal(
    proposal_id: str,
    body: ProposalDecisionRequest,
    service: ProposalReviewService = Depends(get_proposal_review_service),
) -> ProposalView:
    return http_error(
        lambda: ProposalView.from_record(service.reject(proposal_id, body.reason)),
        NOT_FOUND_OR_CONFLICT,
    )
