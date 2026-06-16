from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.api.dependencies import AuthRequestContext, resolve_auth_context
from app.container import AppContainer
from app.db.session import get_session
from app.rag.api.schema import (
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
from app.rag.service.pipeline import GitHubRagPipelineService
from app.rag.service.ports import AnswerUseCase, IndexUseCase

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
    """저장 없이 GitHub 파일 응답이 어떤 RAG 청크로 변환되는지 확인한다."""

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
    index_service: IndexUseCase = Depends(Provide[AppContainer.rag_index_service]),
) -> RagStoredIndexResponseDTO:
    """직접 전달된 GitHub 파일 목록을 SQL과 벡터 DB에 저장한다."""

    return index_service.index_and_store(db, request)


@rag.post(
    "/github/repository/index/store",
    tags=["rag"],
    response_model=RagStoredIndexResponseDTO,
)
@inject
def store_github_repository_rag_index(
    request: GitHubRepositoryIndexRequestDTO,
    auth_context: AuthRequestContext = Depends(resolve_auth_context),
    index_service: IndexUseCase = Depends(Provide[AppContainer.rag_index_service]),
) -> RagStoredIndexResponseDTO:
    """로그인 사용자의 GitHub 토큰으로 레포 파일을 수집해 RAG 저장소에 인덱싱한다."""

    try:
        account = auth_context.github_account()
        return index_service.index_repository_and_store(
            db=auth_context.db,
            request=request,
            github_access_token=account.access_token,
        )
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
    auth_context: AuthRequestContext = Depends(resolve_auth_context),
    answer_service: AnswerUseCase = Depends(Provide[AppContainer.rag_answer_service]),
) -> RagAskResponseDTO:
    """저장된 RAG 근거를 검색하고 LLM 답변과 출처를 함께 반환한다."""

    try:
        auth_context.github_account()
        return answer_service.answer(auth_context.db, request)
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
    index_service: IndexUseCase = Depends(Provide[AppContainer.rag_index_service]),
) -> RagIndexRunListResponseDTO:
    """사용자가 이전 분석 기준을 고를 수 있도록 최근 인덱싱 이력을 반환한다."""

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
    index_service: IndexUseCase = Depends(Provide[AppContainer.rag_index_service]),
) -> RagIndexRunDetailDTO:
    """특정 분석 run의 파일, 청크, 스킵 파일 상세를 조회한다."""

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
    index_service: IndexUseCase = Depends(Provide[AppContainer.rag_index_service]),
) -> RagSqlChunkSearchResponseDTO:
    """정확한 단어 포함 여부를 확인하기 위해 SQL chunk_text 검색을 제공한다."""

    return index_service.search_sql_chunks(db, keyword, limit)


@rag.post(
    "/vector/search",
    tags=["rag"],
    response_model=RagVectorSearchResponseDTO,
)
@inject
def search_rag_chunks_from_vector(
    request: RagVectorSearchRequestDTO,
    index_service: IndexUseCase = Depends(Provide[AppContainer.rag_index_service]),
) -> RagVectorSearchResponseDTO:
    """질문과 의미가 가까운 근거 청크를 벡터 DB에서 찾는다."""

    return index_service.search_vector_chunks(request)
