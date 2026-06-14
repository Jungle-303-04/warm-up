# RAG 관련 HTTP 엔드포인트를 정의하는 FastAPI 라우터 파일
# GitHub 파일 목록을 받아 RAG index 결과를 만드는 API를 제공
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.container import AppContainer
from app.db.session import get_session
from app.domains.auth.api.dependencies import AUTH_COOKIE_NAME, resolve_auth_token
from app.domains.auth.application.auth_service import AuthService
from app.domains.auth.domain.errors import AuthTokenError
from app.domains.rag.api.schema import (
    GitHubRagPipelineRequestDTO,
    GitHubRagPipelineResultDTO,
    GitHubRepositoryIndexRequestDTO,
    RagAskRequestDTO,
    RagAskResponseDTO,
    RagIndexRunDetailDTO,
    RagIndexRunListResponseDTO,
    RagSqlChunkSearchResponseDTO,
    RagStoredIndexResponseDTO,
    RagVectorSearchRequestDTO,
    RagVectorSearchResponseDTO,
)
from app.domains.rag.application.answer_service import RagAnswerService
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


@rag.post(
    "/github/repository/index/store",
    tags=["rag"],
    response_model=RagStoredIndexResponseDTO,
)
@inject
def store_github_repository_rag_index(
    request: GitHubRepositoryIndexRequestDTO,
    authorization: str | None = Header(default=None),
    auth_cookie: str | None = Cookie(default=None, alias=AUTH_COOKIE_NAME),
    db: Session = Depends(get_session),
    auth_service: AuthService = Depends(Provide[AppContainer.auth_service]),
    index_service: RagIndexService = Depends(Provide[AppContainer.rag_index_service]),
) -> RagStoredIndexResponseDTO:
    try:
        account = auth_service.get_authenticated_github_account(
            db=db,
            access_token=resolve_auth_token(authorization, auth_cookie),
        )
        return index_service.index_repository_and_store(
            db=db,
            request=request,
            github_access_token=account.access_token,
        )
    except AuthTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@rag.post(
    "/ask",
    tags=["rag"],
    response_model=RagAskResponseDTO,
)
@inject
def ask_repository_rag(
    request: RagAskRequestDTO,
    authorization: str | None = Header(default=None),
    auth_cookie: str | None = Cookie(default=None, alias=AUTH_COOKIE_NAME),
    db: Session = Depends(get_session),
    auth_service: AuthService = Depends(Provide[AppContainer.auth_service]),
    answer_service: RagAnswerService = Depends(Provide[AppContainer.rag_answer_service]),
) -> RagAskResponseDTO:
    try:
        auth_service.get_authenticated_github_account(
            db=db,
            access_token=resolve_auth_token(authorization, auth_cookie),
        )
        return answer_service.answer(request)
    except AuthTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


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
