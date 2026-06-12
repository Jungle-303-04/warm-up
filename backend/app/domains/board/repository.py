# Board 데이터의 DB 접근 로직을 작성하는 파일
# SQLAlchemy를 사용한 조회, 생성, 수정, 삭제 쿼리 작성
from datetime import datetime

from app.domains.board.schema import CreateBoard, BoardResponse
#sqlmodel

def insert_board(request: CreateBoard) -> BoardResponse:
    now = datetime.utcnow()
    # must edit!!!!!!!!!!!!!!!!!!!
    # TODO: 실제 DB insert 구현 후 생성된 BoardResponse를 반환
    return BoardResponse(
        id=1,
        board_type=request.board_type,
        title=request.title,
        content=request.content,
        tag=request.tag,
        user_id=request.user_id,
        created_at=now,
        updated_at=now,
        assignee_user_ids=request.assignee_user_ids,
        participant_user_ids=request.participant_user_ids,
        carbon_copy_user_ids=request.carbon_copy_user_ids,
    )