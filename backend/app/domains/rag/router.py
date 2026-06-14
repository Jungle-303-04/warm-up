# RAG 관련 HTTP 엔드포인트를 정의하는 FastAPI 라우터 파일
# GitHub 파일 목록을 받아 RAG index 결과를 만드는 API를 제공
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.container import AppContainer
from app.domains.rag.pipeline import GitHubRagPipelineService
from app.domains.rag.schema import (
    GitHubRagPipelineRequestDTO,
    GitHubRagPipelineResultDTO,
)


# rag router
rag = APIRouter(prefix="/rag")


# GitHub files -> RAG index
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
