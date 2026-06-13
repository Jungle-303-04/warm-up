from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.api.router import api_router

logger = logging.getLogger(__name__)


def check_database_connection() -> None:
    logger.info("DB 저장소가 아직 설정되지 않아 DB 연결 확인을 건너뜁니다")


def check_github_app_configuration() -> None:
    logger.info("GitHub App이 아직 설정되지 않아 GitHub 설정 확인을 건너뜁니다")


def check_embedding_provider_configuration() -> None:
    logger.info("임베딩 제공자가 아직 설정되지 않아 임베딩 설정 확인을 건너뜁니다")


def check_worker_queue_connection() -> None:
    logger.info("작업 큐가 아직 설정되지 않아 작업 큐 연결 확인을 건너뜁니다")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
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

app.include_router(api_router)
