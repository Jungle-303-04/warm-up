from fastapi import APIRouter, Depends, HTTPException, status

from app.pipeline import (
    PipelineRequest,
    PipelineResponse,
    PipelineStagesResponse,
    pipeline_stage_payloads,
)
from app.pipeline.dependencies import get_pipeline_service
from app.pipeline.application.service import PipelineService

router = APIRouter()


@router.get(
    "",
    response_model=PipelineStagesResponse,
    status_code=status.HTTP_200_OK,
)
def pipeline() -> PipelineStagesResponse:
    return PipelineStagesResponse(stages=pipeline_stage_payloads())


@router.post(
    "/run",
    response_model=PipelineResponse,
    status_code=status.HTTP_200_OK,
)
def run_pipeline(
    request: PipelineRequest,
    service: PipelineService = Depends(get_pipeline_service),
) -> PipelineResponse:
    try:
        return service.run(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
