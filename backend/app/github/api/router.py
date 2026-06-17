import json
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.api.errors import EntityNotFoundError, http_error
from app.api.responses import BAD_REQUEST_RESPONSE
from app.auth.dependencies import get_current_claims, get_github_token_store
from app.auth.domain.ports import GitHubTokenStore
from app.auth.domain.records import SessionClaims
from app.config import Settings, get_settings
from app.github.api.schemas import (
    GitHubRepoInfoResponse,
    PublishProposalRequest,
    PublishProposalResponse,
    WebhookAcceptedResponse,
)
from app.github.application.publish_service import ProposalPublishService
from app.github.application.webhook_service import GitHubWebhookService
from app.github.dependencies import get_comment_client, get_webhook_service
from app.github.domain.ports import GitHubCommentClient
from app.github.domain.signature import verify_signature
from app.proposals.dependencies import get_proposal_review_service
from app.proposals.service import ProposalReviewService

router = APIRouter()

GITHUB_API_TIMEOUT = 10.0


def _github_headers(access_token: str | None) -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _raise_github_error(response: httpx.Response) -> None:
    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitHub 저장소를 찾을 수 없습니다",
        )
    if response.status_code in (401, 403):
        detail = "GitHub 저장소 정보를 가져오지 못했습니다"
        try:
            payload = response.json()
            detail = str(payload.get("message") or detail)
        except ValueError:
            pass
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub 저장소 정보를 가져오지 못했습니다",
        ) from exc


@router.get("/repos/{owner}/{repo}/info", response_model=GitHubRepoInfoResponse)
def github_repo_info(
    owner: str,
    repo: str,
    claims: SessionClaims = Depends(get_current_claims),
    token_store: GitHubTokenStore = Depends(get_github_token_store),
) -> GitHubRepoInfoResponse:
    access_token = token_store.get(claims.user_id)
    headers = _github_headers(access_token)
    safe_owner = quote(owner, safe="")
    safe_repo = quote(repo, safe="")
    base_url = f"https://api.github.com/repos/{safe_owner}/{safe_repo}"

    try:
        with httpx.Client(timeout=GITHUB_API_TIMEOUT) as client:
            repo_response = client.get(base_url, headers=headers)
            _raise_github_error(repo_response)
            repo_payload = repo_response.json()
            default_branch = str(repo_payload.get("default_branch") or "main")

            branch_response = client.get(
                f"{base_url}/branches?per_page=100",
                headers=headers,
            )
            _raise_github_error(branch_response)
            branch_payload = branch_response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub API 연결에 실패했습니다",
        ) from exc

    branches = [
        str(item.get("name"))
        for item in branch_payload
        if isinstance(item, dict) and item.get("name")
    ]
    if default_branch not in branches:
        branches.insert(0, default_branch)
    return GitHubRepoInfoResponse(
        owner=owner,
        repo=repo,
        defaultBranch=default_branch,
        branches=branches,
    )


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
    proposals: ProposalReviewService = Depends(get_proposal_review_service),
    _claims = Depends(get_current_claims),
) -> PublishProposalResponse:
    def run() -> PublishProposalResponse:
        record = proposals.get(proposal_id)
        url = ProposalPublishService(client=client).publish(record, body.issue_number)
        return PublishProposalResponse(comment_url=url)

    return http_error(run, {EntityNotFoundError: status.HTTP_404_NOT_FOUND})
