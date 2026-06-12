# Board 기능의 비즈니스 로직을 작성하는 파일
# router에서 받은 요청을 처리하고 repository를 통해 DB 작업 조합
from app.domains.board.schema import CreateBoard, BoardResponse
from app.domains.board import repository

from fastapi import HTTPException, status

SCHEDULE_BOARD_TYPE = 1
PROCEEDINGS_BOARD_TYPE = 2

def create_board(request: CreateBoard) -> BoardResponse:
    # Validate supported board type.
    if request.board_type not in {
        SCHEDULE_BOARD_TYPE,
        PROCEEDINGS_BOARD_TYPE,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid board_type",
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

    return repository.insert_board(request)
    