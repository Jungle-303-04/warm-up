# Board 기능의 비즈니스 로직을 작성하는 파일
# router에서 받은 요청을 처리하고 repository를 통해 DB 작업 조합
from app.domains.board.schema import CreateBoard, BoardResponse
from app.domains.board import repository

def create_board(request: CreateBoard) -> BoardResponse:
    return repository.insert_board(request)