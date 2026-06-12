# Board 관련 HTTP 엔드포인트를 정의하는 FastAPI 라우터 파일
# Java의 Controller처럼 요청을 받고 service 계층으로 작업 넘김

from fastapi import APIRouter, HTTPException, status

from app.domains.board.schema import CreateBoard, BoardResponse
from app.domains.board import service

board = APIRouter(prefix = "/board")

# create
@board.post("/", tags=["board"], status_code=status.HTTP_201_CREATED, response_model=BoardResponse)
def create_board(request: CreateBoard):
    created_board = service.create_board(request)

    if created_board is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create board",
        )

    return created_board
        

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