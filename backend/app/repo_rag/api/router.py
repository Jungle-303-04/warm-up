from fastapi import APIRouter, Depends, status

from app.api.errors import http_error
from app.api.responses import BAD_REQUEST_RESPONSE
from app.repo_rag.dependencies import get_repo_rag_sync_service
from app.repo_rag.api.schemas import RepoRagSyncRequest, RepoRagSyncResponse
from app.repo_rag.application.service import RepoRagSyncService

router = APIRouter()


@router.post(
    "/sync",
    response_model=RepoRagSyncResponse,
    status_code=status.HTTP_200_OK,
    responses=BAD_REQUEST_RESPONSE,
)
def sync_repo_rag(
    request: RepoRagSyncRequest,
    service: RepoRagSyncService = Depends(get_repo_rag_sync_service),
) -> RepoRagSyncResponse:
    return http_error(
        lambda: service.run(request),
        {ValueError: status.HTTP_400_BAD_REQUEST},
    )
