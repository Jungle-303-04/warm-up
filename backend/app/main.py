from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.domains.board import model as board_model
from app.domains.board.router import board as board_router
from app.domains.user.model import User


@asynccontextmanager
async def lifespan(app: FastAPI):
    # app start -> create DB tables
    Base.metadata.create_all(bind=engine)

    # create temporary user for board API test
    with SessionLocal() as session:
        user = session.get(User, 1)
        if user is None:
            session.add(User(id=1))
            session.commit()

    yield


app = FastAPI(lifespan=lifespan) # make instance


app.include_router(board_router, tags=["board"])

# get method
@app.get("/")
async def root():
    return{"hello":"world"}
