from fastapi import FastAPI

from app.pipeline import pipeline_stage_payloads
from app.schemas.pipeline import PipelineRequest, PipelineResponse
from app.services.pipeline import PipelineService

# Route layer는 HTTP 요청/응답만 다루고, 실제 파이프라인 흐름은 service에 위임한다.
app = FastAPI(
    title="RepoPilot API",
    version="0.1.0",
    summary="Minimal API surface for the RepoPilot pipeline",
)

# 현재는 메모리 상태가 없는 service라 앱 시작 시 한 번만 만들어도 충분하다.
pipeline_service = PipelineService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/pipeline")
def pipeline() -> dict[str, list[dict[str, str]]]:
    return {"stages": pipeline_stage_payloads()}


@app.post("/pipeline/run")
def run_pipeline(request: PipelineRequest) -> PipelineResponse:
    return pipeline_service.run(request)
