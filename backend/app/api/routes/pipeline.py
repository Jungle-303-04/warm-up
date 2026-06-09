from fastapi import APIRouter

from app.pipeline import pipeline_stage_payloads
from app.schemas.pipeline import PipelineRequest, PipelineResponse
from app.services.pipeline import PipelineService

router = APIRouter()

# 현재는 메모리 상태가 없는 service라 route module에서 한 번만 만들어도 충분하다.
pipeline_service = PipelineService()


@router.get("")
def pipeline() -> dict[str, list[dict[str, str]]]:
    return {"stages": pipeline_stage_payloads()}


@router.post("/run")
def run_pipeline(request: PipelineRequest) -> PipelineResponse:
    return pipeline_service.run(request)
