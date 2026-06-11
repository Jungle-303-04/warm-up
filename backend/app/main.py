from fastapi import FastAPI
from app.domains.board.router import board as board_router


app = FastAPI() # make instance


app.include_router(board_router, tags=["board"])

# get method
@app.get("/")
async def root():
    return{"hello":"world"}