from fastapi import APIRouter, Depends, HTTPException, status

from app.repo_rag.dependencies import get_repo_rag_sync_service
from app.repo_rag.schemas import RepoRagSyncRequest, RepoRagSyncResponse
from app.repo_rag.service import RepoRagSyncService

router = APIRouter()


@router.post(
    "/sync",
    response_model=RepoRagSyncResponse,
    status_code=status.HTTP_200_OK,
)
def sync_repo_rag(
    request: RepoRagSyncRequest,
    service: RepoRagSyncService = Depends(get_repo_rag_sync_service),
) -> RepoRagSyncResponse:
    try:
        return service.run(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
