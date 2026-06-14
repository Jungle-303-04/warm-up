from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.container import AppContainer
from app.domains.rag.pipeline import GitHubRagPipelineService
from app.domains.rag.schema import (
    GitHubRagPipelineRequestDTO,
    GitHubRagPipelineResultDTO,
)


rag = APIRouter(prefix="/rag")


@rag.post(
    "/github/index",
    tags=["rag"],
    response_model=GitHubRagPipelineResultDTO,
)
@inject
def build_github_rag_index(
    request: GitHubRagPipelineRequestDTO,
    pipeline_service: GitHubRagPipelineService = Depends(
        Provide[AppContainer.rag_pipeline_service]
    ),
) -> GitHubRagPipelineResultDTO:
    return pipeline_service.build_index_from_github_files(request)
