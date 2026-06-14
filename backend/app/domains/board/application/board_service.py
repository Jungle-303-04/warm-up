# Board 기능의 비즈니스 로직을 작성하는 파일
# router에서 받은 요청을 처리하고 repository를 통해 DB 작업 조합
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domains.board.api.schema import (
    BoardPageResponse,
    BoardResponse,
    BoardSearchParams,
    CreateBoard,
    UpdateBoard,
)
from app.domains.board.infrastructure import repository

BASIC_BOARD_TYPE = 1
SCHEDULE_BOARD_TYPE = 2
PROCEEDINGS_BOARD_TYPE = 3


def validate_board_request(request: CreateBoard | UpdateBoard) -> None:
    # Validate supported board type.
    if request.board_type not in {
        BASIC_BOARD_TYPE,
        SCHEDULE_BOARD_TYPE,
        PROCEEDINGS_BOARD_TYPE,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid board_type",
        )
    
    # Validate basic boards do not include details of other type
    if request.board_type == BASIC_BOARD_TYPE:
        if (
            request.schedule_board_detail is not None
            or request.schedule_board_tasks
            or request.proceedings_board_detail is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="detail fields are not allowed for basic board",
            )

    if request.board_type == SCHEDULE_BOARD_TYPE:
        if request.schedule_board_detail is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="schedule_board_detail is required",
            )

        # Validate board type and detail consistency.
        if request.proceedings_board_detail is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="proceedings detail is only allowed for proceedings board",
            )

        # Validate schedule time range.
        if request.schedule_board_detail.start_at >= request.schedule_board_detail.end_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_at must be earlier than end_at",
            )

    elif request.board_type == PROCEEDINGS_BOARD_TYPE:
        if request.proceedings_board_detail is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="proceedings_board_detail is required",
            )

        # Validate board type and detail consistency.
        if request.schedule_board_detail is not None or request.schedule_board_tasks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="schedule fields are only allowed for schedule board",
            )

def create_board(db: Session, request: CreateBoard) -> BoardResponse:
    validate_board_request(request)
    return repository.insert_board(db, request)


# read all
def read_boards(db: Session, search_params: BoardSearchParams) -> BoardPageResponse:
    return repository.select_boards(db, search_params)


# read by id
def read_board(db: Session, board_id: int) -> BoardResponse:
    board = repository.select_board(db, board_id)

    if board is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="board not found",
        )

    return board


# update by id
def update_board(db: Session, board_id: int, request: UpdateBoard) -> BoardResponse:
    validate_board_request(request)
    board = repository.update_board(db, board_id, request)

    if board is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="board not found",
        )

    return board


# delete by id
def delete_board(db: Session, board_id: int) -> None:
    deleted = repository.delete_board(db, board_id)

    if deleted is False:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="board not found",
        )
