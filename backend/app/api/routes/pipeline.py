from fastapi import APIRouter, HTTPException

from app.pipeline import pipeline_stage_payloads
from app.schemas.pipeline import PipelineRequest, PipelineResponse
from app.schemas.repo_rag import RepoRagSyncRequest, RepoRagSyncResponse
from app.services.pipeline import PipelineService
from app.services.repo_rag_sync import RepoRagSyncService

router = APIRouter()

pipeline_service = PipelineService()
repo_rag_sync_service = RepoRagSyncService()


@router.get("")
def pipeline() -> dict[str, list[dict[str, str]]]:
    return {"stages": pipeline_stage_payloads()}


@router.post("/run")
def run_pipeline(request: PipelineRequest) -> PipelineResponse:
    try:
        return pipeline_service.run(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sync")
def sync_repo_rag(request: RepoRagSyncRequest) -> RepoRagSyncResponse:
    try:
        return repo_rag_sync_service.run(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
