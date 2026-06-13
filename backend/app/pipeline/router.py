from fastapi import APIRouter, Depends, HTTPException

from app.pipeline import PipelineRequest, PipelineResponse, pipeline_stage_payloads
from app.pipeline.dependencies import get_pipeline_service
from app.pipeline.service import PipelineService

router = APIRouter()


@router.get("")
def pipeline() -> dict[str, list[dict[str, str]]]:
    return {"stages": pipeline_stage_payloads()}


@router.post("/run")
def run_pipeline(
    request: PipelineRequest,
    service: PipelineService = Depends(get_pipeline_service),
) -> PipelineResponse:
    try:
        return service.run(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
