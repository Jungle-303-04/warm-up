from fastapi import FastAPI

from app.modules.pipeline import PipelineService
from app.pipeline import PIPELINE_STAGES
from app.schemas import PipelineRequest, PipelineResponse

app = FastAPI(
    title="RepoPilot API",
    version="0.1.0",
    summary="Minimal API surface for the RepoPilot pipeline",
)

pipeline_service = PipelineService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/pipeline")
def pipeline() -> dict[str, list[dict[str, str]]]:
    return {"stages": PIPELINE_STAGES}


@app.post("/pipeline/run")
def run_pipeline(request: PipelineRequest) -> PipelineResponse:
    return pipeline_service.run(request)
