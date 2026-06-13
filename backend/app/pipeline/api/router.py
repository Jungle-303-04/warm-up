from fastapi import APIRouter, Depends, status

from app.api.errors import http_error
from app.api.responses import BAD_REQUEST_RESPONSE
from app.pipeline import (
    PipelineRequest,
    PipelineResponse,
)
from app.pipeline.dependencies import get_pipeline_service
from app.pipeline.application.service import PipelineService

router = APIRouter()


@router.post(
    "/run",
    response_model=PipelineResponse,
    status_code=status.HTTP_200_OK,
    responses=BAD_REQUEST_RESPONSE,
)
def run_pipeline(
    request: PipelineRequest,
    service: PipelineService = Depends(get_pipeline_service),
) -> PipelineResponse:
    return http_error(
        lambda: service.run(request),
        {ValueError: status.HTTP_400_BAD_REQUEST},
    )
