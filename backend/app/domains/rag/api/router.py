# RAG 관련 HTTP 엔드포인트를 정의하는 FastAPI 라우터 파일
# GitHub 파일 목록을 받아 RAG index 결과를 만드는 API를 제공
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.container import AppContainer
from app.db.session import get_session
from app.domains.rag.api.schema import (
    GitHubRagPipelineRequestDTO,
    GitHubRagPipelineResultDTO,
    RagIndexRunDetailDTO,
    RagIndexRunListResponseDTO,
    RagSqlChunkSearchResponseDTO,
    RagStoredIndexResponseDTO,
    RagVectorSearchRequestDTO,
    RagVectorSearchResponseDTO,
)
from app.domains.rag.application.index_service import RagIndexService
from app.domains.rag.application.pipeline import GitHubRagPipelineService


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


@rag.post(
    "/github/index/store",
    tags=["rag"],
    response_model=RagStoredIndexResponseDTO,
)
@inject
def store_github_rag_index(
    request: GitHubRagPipelineRequestDTO,
    db: Session = Depends(get_session),
    index_service: RagIndexService = Depends(Provide[AppContainer.rag_index_service]),
) -> RagStoredIndexResponseDTO:
    return index_service.index_and_store(db, request)


@rag.get(
    "/runs",
    tags=["rag"],
    response_model=RagIndexRunListResponseDTO,
)
@inject
def list_rag_index_runs(
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_session),
    index_service: RagIndexService = Depends(Provide[AppContainer.rag_index_service]),
) -> RagIndexRunListResponseDTO:
    return index_service.list_runs(db, limit)


@rag.get(
    "/runs/{run_id}",
    tags=["rag"],
    response_model=RagIndexRunDetailDTO,
)
@inject
def get_rag_index_run(
    run_id: int,
    db: Session = Depends(get_session),
    index_service: RagIndexService = Depends(Provide[AppContainer.rag_index_service]),
) -> RagIndexRunDetailDTO:
    run_detail = index_service.get_run_detail(db, run_id)

    if run_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="rag index run not found",
        )

    return run_detail


@rag.get(
    "/chunks/search",
    tags=["rag"],
    response_model=RagSqlChunkSearchResponseDTO,
)
@inject
def search_rag_chunks_from_sql(
    keyword: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_session),
    index_service: RagIndexService = Depends(Provide[AppContainer.rag_index_service]),
) -> RagSqlChunkSearchResponseDTO:
    return index_service.search_sql_chunks(db, keyword, limit)


@rag.post(
    "/vector/search",
    tags=["rag"],
    response_model=RagVectorSearchResponseDTO,
)
@inject
def search_rag_chunks_from_vector(
    request: RagVectorSearchRequestDTO,
    index_service: RagIndexService = Depends(Provide[AppContainer.rag_index_service]),
) -> RagVectorSearchResponseDTO:
    return index_service.search_vector_chunks(request)
