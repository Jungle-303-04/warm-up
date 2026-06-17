from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.container import container
from app.db.base import Base
from app.db.session import engine
from app.agent.api import router as agent_router_module
from app.auth.api import dependencies as auth_dependencies_module
from app.auth.api import router as auth_router_module
from app.auth.external import model as auth_model
from app.board.api import router as board_router_module
from app.board.external import model as board_model
from app.rag.api import router as rag_router_module
from app.rag.external import model as rag_model


def wire_container(app: FastAPI) -> None:
    """FastAPI 라우터 함수가 dependency-injector provider를 사용할 수 있게 연결한다."""

    app.container = container
    container.wire(
        modules=[
            agent_router_module,
            auth_dependencies_module,
            rag_router_module,
            auth_router_module,
            board_router_module,
        ]
    )


def check_database_connection() -> None:
    """서버 시작 시 PostgreSQL 연결 실패를 빠르게 드러낸다."""

    with engine.connect() as connection:
        connection.execute(text("select 1"))


def check_vector_database_connection() -> None:
    """서버 시작 시 Chroma collection 접근 가능 여부를 확인한다."""

    container.rag_vector_repository().count()


def create_database_tables() -> None:
    """개발 단계에서 ORM 모델 기준으로 필요한 테이블을 자동 생성한다."""

    Base.metadata.create_all(bind=engine)


def unwire_container() -> None:
    """앱 종료 시 라우터에 연결된 provider wiring을 정리한다."""

    container.unwire()


def configure_cors(app: FastAPI) -> None:
    """로컬 백엔드와 Vercel 프론트가 개발/시연 중 서로 API를 호출하게 허용한다."""

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """서버 시작 전 DB/벡터 DB 점검과 DI 연결을 수행하고 종료 시 wiring을 해제한다."""

    wire_container(app)
    check_database_connection()
    check_vector_database_connection()
    create_database_tables()

    yield

    unwire_container()


app = FastAPI(lifespan=lifespan)
configure_cors(app)

app.include_router(board_router_module.board, tags=["board"])
app.include_router(auth_router_module.auth, tags=["auth"])
app.include_router(rag_router_module.rag, tags=["rag"])
app.include_router(agent_router_module.agent, tags=["agent"])


@app.get("/")
async def root():
    return {"hello": "world"}
