# FastAPI 애플리케이션 진입점을 정의하는 파일
# 서버 시작/종료 처리, router 등록, DI container 연결을 담당
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.container import container
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.domains.board import model as board_model
from app.domains.board.router import board as board_router
from app.domains.rag import router as rag_router_module
from app.domains.user.model import User


# dependency container 연결
def wire_dependency_container(app: FastAPI) -> None:
    app.container = container
    container.wire(modules=[rag_router_module])


# DB table 준비
def create_database_tables() -> None:
    Base.metadata.create_all(bind=engine)


# board API 테스트용 기본 user 준비
def create_test_user() -> None:
    with SessionLocal() as session:
        user = session.get(User, 1)
        if user is None:
            session.add(User(id=1))
            session.commit()


# dependency container 연결 해제
def unwire_dependency_container() -> None:
    container.unwire()


# app lifespan
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    wire_dependency_container(app)
    create_database_tables()
    create_test_user()

    yield
    unwire_dependency_container()


app = FastAPI(lifespan=lifespan) # make instance

# router registration
app.include_router(board_router, tags=["board"])
app.include_router(rag_router_module.rag, tags=["rag"])

# get method
@app.get("/")
async def root():
    return{"hello":"world"}
