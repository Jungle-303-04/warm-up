# Board 관련 HTTP 엔드포인트를 정의하는 FastAPI 라우터 파일
# Java의 Controller처럼 요청을 받고 service 계층으로 작업 넘김

from fastapi import APIRouter

from app.domains.board.schema import CreateBoard

board = APIRouter(prefix = "/board")

# create
@board.post("/", tags=["board"])
async def create_board(request: CreateBoard):
    return {"msg":"success"}

# # read
# @board.get("/", tags=["board"])
# async def read_board(request: ReadBoard):
#     return {"msg":"let go"}

# # update
# @board.put("/", tags=["board"])
# async def update_board(request: UpdateBoard):
#     return {"msg":"let go"}

# # delete
# @board.delete("/", tags=["board"])
# async def delete_board(request: DeleteBoard):
#     return {"msg":"let go"}