from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.container import AppContainer
from app.db.session import get_session
from app.board.api.schema import (
    BoardPageResponse,
    BoardResponse,
    BoardSearchParams,
    CreateBoard,
    UpdateBoard,
)
from app.board.service.ports import BoardServicePort


board = APIRouter(prefix="/board")


@board.post(
    "/",
    tags=["board"],
    status_code=status.HTTP_201_CREATED,
    response_model=BoardResponse,
)
@inject
def create_board(
    request: CreateBoard,
    db: Session = Depends(get_session),
    board_service: BoardServicePort = Depends(Provide[AppContainer.board_service]),
) -> BoardResponse:
    """새 보드와 타입별 상세 정보를 저장한다."""

    return board_service.create_board(db, request)


@board.get("/", tags=["board"], response_model=BoardPageResponse)
@inject
def read_boards(
    search_params: BoardSearchParams = Depends(),
    db: Session = Depends(get_session),
    board_service: BoardServicePort = Depends(Provide[AppContainer.board_service]),
) -> BoardPageResponse:
    """검색 조건과 페이지 조건에 맞는 보드 목록을 반환한다."""

    return board_service.read_boards(db, search_params)


@board.get("/{board_id}", tags=["board"], response_model=BoardResponse)
@inject
def read_board(
    board_id: int,
    db: Session = Depends(get_session),
    board_service: BoardServicePort = Depends(Provide[AppContainer.board_service]),
) -> BoardResponse:
    """단일 보드의 본문, 상세, 관련 사용자 정보를 조회한다."""

    return board_service.read_board(db, board_id)


@board.put("/{board_id}", tags=["board"], response_model=BoardResponse)
@inject
def update_board(
    board_id: int,
    request: UpdateBoard,
    db: Session = Depends(get_session),
    board_service: BoardServicePort = Depends(Provide[AppContainer.board_service]),
) -> BoardResponse:
    """보드 본문과 타입별 상세 정보를 요청 값으로 교체한다."""

    return board_service.update_board(db, board_id, request)


@board.delete("/{board_id}", tags=["board"], status_code=status.HTTP_204_NO_CONTENT)
@inject
def delete_board(
    board_id: int,
    db: Session = Depends(get_session),
    board_service: BoardServicePort = Depends(Provide[AppContainer.board_service]),
) -> None:
    """보드와 연결된 상세/관계 데이터를 함께 삭제한다."""

    board_service.delete_board(db, board_id)
