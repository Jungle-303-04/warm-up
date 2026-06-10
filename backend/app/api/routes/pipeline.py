from fastapi import APIRouter

from app.pipeline import pipeline_stage_payloads
from app.schemas.pipeline import PipelineRequest, PipelineResponse
from app.services.pipeline import PipelineService

router = APIRouter()

pipeline_service = PipelineService()


@router.get("")
def pipeline() -> dict[str, list[dict[str, str]]]:
    return {"stages": pipeline_stage_payloads()}


@router.post("/run")
def run_pipeline(request: PipelineRequest) -> PipelineResponse:
    return pipeline_service.run(request)
