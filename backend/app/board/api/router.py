from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.api.dependencies import AuthRequestContext, resolve_auth_context
from app.container import AppContainer
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
    auth_context: AuthRequestContext = Depends(resolve_auth_context),
    board_service: BoardServicePort = Depends(Provide[AppContainer.board_service]),
) -> BoardResponse:
    """새 보드와 타입별 상세 정보를 저장한다."""

    user_id = auth_context.user_id(fallback_user_id=request.user_id)
    return board_service.create_board(
        auth_context.db,
        request.model_copy(update={"user_id": user_id}),
    )


@board.get("/", tags=["board"], response_model=BoardPageResponse)
@inject
def read_boards(
    search_params: BoardSearchParams = Depends(),
    auth_context: AuthRequestContext = Depends(resolve_auth_context),
    board_service: BoardServicePort = Depends(Provide[AppContainer.board_service]),
) -> BoardPageResponse:
    """검색 조건과 페이지 조건에 맞는 보드 목록을 반환한다."""

    user_id = auth_context.user_id(fallback_user_id=search_params.user_id)
    return board_service.read_boards(
        auth_context.db,
        search_params.model_copy(update={"user_id": user_id}),
    )


@board.get("/{board_id}", tags=["board"], response_model=BoardResponse)
@inject
def read_board(
    board_id: int,
    user_id: int | None = None,
    auth_context: AuthRequestContext = Depends(resolve_auth_context),
    board_service: BoardServicePort = Depends(Provide[AppContainer.board_service]),
) -> BoardResponse:
    """단일 보드의 본문, 상세, 관련 사용자 정보를 조회한다."""

    board_response = board_service.read_board(auth_context.db, board_id)
    user_id = auth_context.user_id(fallback_user_id=user_id)
    assert_board_owner(board_response, user_id)
    return board_response


@board.put("/{board_id}", tags=["board"], response_model=BoardResponse)
@inject
def update_board(
    board_id: int,
    request: UpdateBoard,
    auth_context: AuthRequestContext = Depends(resolve_auth_context),
    board_service: BoardServicePort = Depends(Provide[AppContainer.board_service]),
) -> BoardResponse:
    """보드 본문과 타입별 상세 정보를 요청 값으로 교체한다."""

    current_board = board_service.read_board(auth_context.db, board_id)
    user_id = auth_context.user_id(fallback_user_id=request.user_id)
    assert_board_owner(current_board, user_id)
    return board_service.update_board(
        auth_context.db,
        board_id,
        request.model_copy(update={"user_id": user_id}),
    )


@board.delete("/{board_id}", tags=["board"], status_code=status.HTTP_204_NO_CONTENT)
@inject
def delete_board(
    board_id: int,
    user_id: int | None = None,
    auth_context: AuthRequestContext = Depends(resolve_auth_context),
    board_service: BoardServicePort = Depends(Provide[AppContainer.board_service]),
) -> None:
    """보드와 연결된 상세/관계 데이터를 함께 삭제한다."""

    board_response = board_service.read_board(auth_context.db, board_id)
    user_id = auth_context.user_id(fallback_user_id=user_id)
    assert_board_owner(board_response, user_id)
    board_service.delete_board(auth_context.db, board_id)


def assert_board_owner(board_response: BoardResponse, user_id: int) -> None:
    """다른 사용자의 보드 id를 직접 찍어 조회/수정/삭제하지 못하게 막는다."""

    if board_response.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="board not found",
        )
