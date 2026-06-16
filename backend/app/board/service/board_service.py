from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.board.api.schema import (
    BoardPageResponse,
    BoardResponse,
    BoardSearchParams,
    CreateBoard,
    UpdateBoard,
)
from app.board.service.ports import BoardRepositoryPort


BASIC_BOARD_TYPE = 1
SCHEDULE_BOARD_TYPE = 2
PROCEEDINGS_BOARD_TYPE = 3
SUPPORTED_BOARD_TYPES = {
    BASIC_BOARD_TYPE,
    SCHEDULE_BOARD_TYPE,
    PROCEEDINGS_BOARD_TYPE,
}


class BoardService:
    """보드 타입별 입력 규칙을 검증한 뒤 저장소에 실제 CRUD를 위임한다."""

    def __init__(self, board_repository: BoardRepositoryPort) -> None:
        self.board_repository = board_repository

    def create_board(self, db: Session, request: CreateBoard) -> BoardResponse:
        self.validate_board_request(request)
        return self.board_repository.insert(db, request)

    def read_boards(
        self,
        db: Session,
        search_params: BoardSearchParams,
    ) -> BoardPageResponse:
        return self.board_repository.select_page(db, search_params)

    def read_board(self, db: Session, board_id: int) -> BoardResponse:
        board = self.board_repository.select_one(db, board_id)
        if board is None:
            raise_not_found()
        return board

    def update_board(
        self,
        db: Session,
        board_id: int,
        request: UpdateBoard,
    ) -> BoardResponse:
        self.validate_board_request(request)
        board = self.board_repository.update(db, board_id, request)
        if board is None:
            raise_not_found()
        return board

    def delete_board(self, db: Session, board_id: int) -> None:
        deleted = self.board_repository.delete(db, board_id)
        if deleted is False:
            raise_not_found()

    def validate_board_request(self, request: CreateBoard | UpdateBoard) -> None:
        """서로 다른 보드 타입의 상세 필드가 섞이지 않게 생성/수정 전에 검사한다."""

        validate_board_user(request)
        validate_supported_board_type(request)
        validate_basic_board(request)
        validate_schedule_board(request)
        validate_proceedings_board(request)


def validate_board_user(request: CreateBoard | UpdateBoard) -> None:
    """라우터가 로그인 사용자 기준의 내부 user_id를 주입했는지 확인한다."""

    if request.user_id is None:
        raise_bad_request("user_id is required")


def validate_supported_board_type(request: CreateBoard | UpdateBoard) -> None:
    """알 수 없는 board_type이 저장소까지 내려가지 않도록 막는다."""

    if request.board_type not in SUPPORTED_BOARD_TYPES:
        raise_bad_request("invalid board_type")


def validate_basic_board(request: CreateBoard | UpdateBoard) -> None:
    """기본 보드는 일정/회의 상세를 가질 수 없다는 규칙을 지킨다."""

    if request.board_type != BASIC_BOARD_TYPE:
        return

    if (
        request.schedule_board_detail is not None
        or request.schedule_board_tasks
        or request.proceedings_board_detail is not None
    ):
        raise_bad_request("detail fields are not allowed for basic board")


def validate_schedule_board(request: CreateBoard | UpdateBoard) -> None:
    """일정 보드가 기간과 중요도 상세를 반드시 갖고, 회의 상세와 섞이지 않게 한다."""

    if request.board_type != SCHEDULE_BOARD_TYPE:
        return

    if request.schedule_board_detail is None:
        raise_bad_request("schedule_board_detail is required")

    if request.proceedings_board_detail is not None:
        raise_bad_request("proceedings detail is only allowed for proceedings board")

    if request.schedule_board_detail.start_at >= request.schedule_board_detail.end_at:
        raise_bad_request("start_at must be earlier than end_at")


def validate_proceedings_board(request: CreateBoard | UpdateBoard) -> None:
    """회의록 보드가 회의 일자만 갖고 일정 상세와 섞이지 않게 한다."""

    if request.board_type != PROCEEDINGS_BOARD_TYPE:
        return

    if request.proceedings_board_detail is None:
        raise_bad_request("proceedings_board_detail is required")

    if request.schedule_board_detail is not None or request.schedule_board_tasks:
        raise_bad_request("schedule fields are only allowed for schedule board")


def raise_bad_request(detail: str) -> None:
    """입력 규칙 위반을 HTTP 400으로 통일해 라우터가 예외 변환을 반복하지 않게 한다."""

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail,
    )


def raise_not_found() -> None:
    """없는 보드 접근을 HTTP 404로 통일한다."""

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="board not found",
    )
