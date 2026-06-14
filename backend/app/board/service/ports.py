from typing import Protocol

from sqlalchemy.orm import Session

from app.board.api.schema import (
    BoardPageResponse,
    BoardResponse,
    BoardSearchParams,
    CreateBoard,
    UpdateBoard,
)


class BoardRepositoryPort(Protocol):
    def insert(self, db: Session, request: CreateBoard) -> BoardResponse: ...

    def select_page(
        self,
        db: Session,
        search_params: BoardSearchParams,
    ) -> BoardPageResponse: ...

    def select_one(self, db: Session, board_id: int) -> BoardResponse | None: ...

    def update(
        self,
        db: Session,
        board_id: int,
        request: UpdateBoard,
    ) -> BoardResponse | None: ...

    def delete(self, db: Session, board_id: int) -> bool: ...


class BoardServicePort(Protocol):
    def create_board(self, db: Session, request: CreateBoard) -> BoardResponse: ...

    def read_boards(
        self,
        db: Session,
        search_params: BoardSearchParams,
    ) -> BoardPageResponse: ...

    def read_board(self, db: Session, board_id: int) -> BoardResponse: ...

    def update_board(
        self,
        db: Session,
        board_id: int,
        request: UpdateBoard,
    ) -> BoardResponse: ...

    def delete_board(self, db: Session, board_id: int) -> None: ...
