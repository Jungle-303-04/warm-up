from fastapi import APIRouter, Depends, Response, status

from app.api.errors import http_error
from app.api.responses import BAD_REQUEST_RESPONSE
from app.config import Settings, get_settings
from app.repo_rag.api.schemas import (
    RepoRagSearchHit,
    RepoRagSearchRequest,
    RepoRagSearchResponse,
    RepoRagSyncRequest,
    SyncJobAcceptedResponse,
    SyncJobDetailResponse,
)
from app.repo_rag.application.service import RepoRagSyncService
from app.repo_rag.application.types import UowFactory
from app.repo_rag.dependencies import (
    get_repo_rag_search_service,
    get_repo_rag_sync_service,
    get_uow_factory,
)

router = APIRouter()


@router.post("/sync", status_code=status.HTTP_200_OK, responses=BAD_REQUEST_RESPONSE)
def sync_repo_rag(
    request: RepoRagSyncRequest,
    response: Response,
    settings: Settings = Depends(get_settings),
    service: RepoRagSyncService = Depends(get_repo_rag_sync_service),
):
    # Postgres: 큐에 넣고 즉시 202 반환(워커가 처리). in-memory: 같은 프로세스라 인라인 실행.
    if settings.uses_postgres:

        def enqueue() -> SyncJobAcceptedResponse:
            job = service.enqueue(request)
            response.status_code = status.HTTP_202_ACCEPTED
            return SyncJobAcceptedResponse(job=job.to_view())

        return http_error(enqueue, {ValueError: status.HTTP_400_BAD_REQUEST})

    return http_error(
        lambda: service.run(request),
        {ValueError: status.HTTP_400_BAD_REQUEST},
    )


@router.get(
    "/sync/{job_id}",
    response_model=SyncJobDetailResponse,
    responses=BAD_REQUEST_RESPONSE,
)
def get_sync_job(
    job_id: str,
    uow_factory: UowFactory = Depends(get_uow_factory),
) -> SyncJobDetailResponse:
    def fetch() -> SyncJobDetailResponse:
        with uow_factory() as uow:
            job = uow.repo_rag.get_job(job_id)
            events = uow.repo_rag.job_events(job.id)
            return SyncJobDetailResponse(
                job=job.to_view(),
                events=[event.to_view() for event in events],
            )

    return http_error(fetch, {KeyError: status.HTTP_404_NOT_FOUND})


@router.post(
    "/search",
    response_model=RepoRagSearchResponse,
    status_code=status.HTTP_200_OK,
    responses=BAD_REQUEST_RESPONSE,
)
def search_repo_rag(
    request: RepoRagSearchRequest,
    service=Depends(get_repo_rag_search_service),
) -> RepoRagSearchResponse:
    def run() -> RepoRagSearchResponse:
        hits = service.search(request)
        return RepoRagSearchResponse(
            query=request.query,
            hits=[
                RepoRagSearchHit(
                    chunk=hit.chunk,
                    score=hit.score,
                    vector_score=hit.vector_score,
                    keyword_score=hit.keyword_score,
                )
                for hit in hits
            ],
        )

    return http_error(run, {ValueError: status.HTTP_400_BAD_REQUEST})
