import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    logger.info("GitHub App이 아직 설정되지 않아 GitHub 설정 확인을 건너뜁니다")


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

allowed_origins = {
    get_settings().web_app_url,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
