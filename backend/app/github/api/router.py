import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.api.errors import EntityNotFoundError, http_error
from app.api.responses import BAD_REQUEST_RESPONSE
from app.auth.dependencies import get_current_claims
from app.config import Settings, get_settings
from app.github.api.schemas import (
    PublishProposalRequest,
    PublishProposalResponse,
    WebhookAcceptedResponse,
)
from app.github.application.publish_service import ProposalPublishService
from app.github.application.webhook_service import GitHubWebhookService
from app.github.dependencies import get_comment_client, get_webhook_service
from app.github.domain.ports import GitHubCommentClient
from app.github.domain.signature import verify_signature
from app.proposals.service import ProposalReviewService

router = APIRouter()


@router.post("/webhook", response_model=WebhookAcceptedResponse)
async def github_webhook(
    request: Request,
    x_github_event: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    service: GitHubWebhookService = Depends(get_webhook_service),
) -> WebhookAcceptedResponse:
    secret = settings.github_webhook_secret
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub 웹훅 시크릿이 설정되지 않았습니다",
        )

    body = await request.body()
    if not verify_signature(secret, body, x_hub_signature_256):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="웹훅 서명 검증에 실패했습니다",
        )

    if x_github_event == "ping":
        return WebhookAcceptedResponse(status="pong", event="ping")
    if x_github_event != "push":
        return WebhookAcceptedResponse(status="ignored", event=x_github_event)

    try:
        payload = json.loads(body)
        event = service.handle_push(payload)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return WebhookAcceptedResponse(
        status="accepted",
        event="push",
        repository=event.repository_full_name,
        branch=event.branch,
    )


@router.post(
    "/proposals/{proposal_id}/publish",
    response_model=PublishProposalResponse,
    responses=BAD_REQUEST_RESPONSE,
)
def publish_proposal(
    proposal_id: str,
    body: PublishProposalRequest,
    client: GitHubCommentClient = Depends(get_comment_client),
    proposals: ProposalReviewService = Depends(ProposalReviewService),
    _claims = Depends(get_current_claims),
) -> PublishProposalResponse:
    def run() -> PublishProposalResponse:
        record = proposals.get(proposal_id)
        url = ProposalPublishService(client=client).publish(record, body.issue_number)
        return PublishProposalResponse(comment_url=url)

    return http_error(run, {EntityNotFoundError: status.HTTP_404_NOT_FOUND})
