import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.errors import (
    DomainConflictError,
    DomainValidationError,
    EntityNotFoundError,
)
from app.api.router import api_router
from app.config import get_settings

logger = logging.getLogger(__name__)


def check_database_connection() -> None:
    settings = get_settings()
    if settings.uses_postgres:
        logger.info("Postgres 저장소로 repo-rag를 구동합니다")
    else:
        logger.info("POSTGRES_DATABASE_URL 미설정 — in-memory 저장소로 동작합니다")


def check_github_app_configuration() -> None:
    from app.github.verifier import MockGitHubAppConfigVerifier, RealGitHubAppConfigVerifier
    settings = get_settings()
    # local 또는 postgres가 활성화되지 않았을 때는 Mock 검증기,
    # 상용 환경 등에서는 Real 검증기를 가동
    if settings.repolm_env == "local":
        verifier = MockGitHubAppConfigVerifier()
    else:
        verifier = RealGitHubAppConfigVerifier(settings)
    verifier.verify()


def check_embedding_provider_configuration() -> None:
    settings = get_settings()
    logger.info(
        "임베딩 제공자=%s, 모델=%s, 차원=%s",
        settings.embedding_provider,
        settings.embedding_model,
        settings.embedding_dimension,
    )


def check_worker_queue_connection() -> None:
    logger.info("작업 큐가 아직 설정되지 않아 작업 큐 연결 확인을 건너뜁니다")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info("GitRAG API 서버를 시작합니다")
    check_database_connection()
    check_github_app_configuration()
    check_embedding_provider_configuration()
    check_worker_queue_connection()
    yield
    logger.info("GitRAG API 서버를 종료합니다")


app = FastAPI(
    title="GitRAG API",
    version="0.1.0",
    summary="Git 저장소 기반 RAG 자동화 API",
    license_info={"name": "MIT"},
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(request: Request, exc: EntityNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.exception_handler(KeyError)
async def key_error_handler(request: Request, exc: KeyError):
    # KeyError의 인자가 문자열이 아닐 수도 있으므로 강제 형변환
    key_str = str(exc.args[0]) if exc.args else str(exc)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": f"요청한 리소스를 찾을 수 없습니다: {key_str}"},
    )


@app.exception_handler(DomainValidationError)
async def domain_validation_handler(request: Request, exc: DomainValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(DomainConflictError)
async def domain_conflict_handler(request: Request, exc: DomainConflictError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # 에러가 Request Body(DTO)에서 발생한 것인지 판별
    is_body_error = any(err.get("loc", []) and err.get("loc")[0] == "body" for err in errors)

    if is_body_error:
        detail = (
            errors[0].get("msg", "입력 데이터 유효성 검증 실패")
            if errors
            else "입력 데이터 유효성 검증 실패"
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": detail},
        )

    # 쿼리 파라미터나 경로 파라미터 오류 등은 FastAPI의 기본 422 처리기로 위임
    from fastapi.exception_handlers import request_validation_exception_handler
    return await request_validation_exception_handler(request, exc)





allowed_origins = get_settings().allowed_web_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
