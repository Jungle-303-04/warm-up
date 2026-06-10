from fastapi import FastAPI
from app.domains.board.router import router as board_router


app = FastAPI() # make instance


app.include_router(board_router, prefix="/boards", tags=["boards"])

# get method # for test!
@app.get("/")
def root():
    return{"hello":"world"}