# Board 관련 HTTP 엔드포인트를 정의하는 FastAPI 라우터 파일
# Java의 Controller처럼 요청을 받고 service 계층으로 작업 넘김

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.domains.board.api.schema import (
    BoardPageResponse,
    BoardResponse,
    BoardSearchParams,
    CreateBoard,
    UpdateBoard,
)
from app.domains.board.application import board_service

board = APIRouter(prefix = "/board")

# create
@board.post("/", tags=["board"], status_code=status.HTTP_201_CREATED, response_model=BoardResponse)
def create_board(request: CreateBoard, db: Session = Depends(get_session)):
    return board_service.create_board(db, request)


# read
@board.get("/", tags=["board"], response_model=BoardPageResponse)
def read_boards(
    search_params: BoardSearchParams = Depends(),
    db: Session = Depends(get_session),
):
    return board_service.read_boards(db, search_params)


@board.get("/{board_id}", tags=["board"], response_model=BoardResponse)
def read_board(board_id: int, db: Session = Depends(get_session)):
    return board_service.read_board(db, board_id)


# update
@board.put("/{board_id}", tags=["board"], response_model=BoardResponse)
def update_board(board_id: int, request: UpdateBoard, db: Session = Depends(get_session)):
    return board_service.update_board(db, board_id, request)


# delete
@board.delete("/{board_id}", tags=["board"], status_code=status.HTTP_204_NO_CONTENT)
def delete_board(board_id: int, db: Session = Depends(get_session)):
    board_service.delete_board(db, board_id)
