# Board 데이터의 DB 접근 로직을 작성하는 파일
# SQLAlchemy를 사용한 조회, 생성, 수정, 삭제 쿼리 작성
from sqlalchemy.orm import Session

from app.domains.board.model import (
    Board,
    BoardAssignee,
    BoardCarbonCopy,
    BoardParticipant,
    ProceedingsBoardDetail,
    ScheduleBoardDetail,
    ScheduleBoardTask,
)
from app.domains.board.schema import (
    BoardResponse,
    CreateBoard,
    ResponseProceedingsBoardDetail,
    ResponseScheduleBoardDetail,
    ResponseScheduleBoardTaskDetail,
)

def insert_board(db: Session, request: CreateBoard) -> BoardResponse:
    try:
        # base board
        board = Board(
            board_type=request.board_type,
            title=request.title,
            content=request.content,
            tag=request.tag,
            user_id=request.user_id,
        )

        db.add(board)
        db.flush() # Get board.id before commit.

        # Default values for type-specific response DTO fields.
        schedule_detail_response = None
        schedule_task_responses = []
        schedule_tasks = []
        proceedings_detail_response = None

        ## type-specific detail data
        # detail: schedule
        if request.schedule_board_detail is not None:
            schedule_detail = ScheduleBoardDetail(
                board_id=board.id,
                start_at=request.schedule_board_detail.start_at,
                end_at=request.schedule_board_detail.end_at,
                importance=request.schedule_board_detail.importance,
            )
            db.add(schedule_detail)

            schedule_detail_response = ResponseScheduleBoardDetail(
                board_id=schedule_detail.board_id,
                start_at=schedule_detail.start_at,
                end_at=schedule_detail.end_at,
                importance=schedule_detail.importance,
            )

            # detail: schedule task detail
            schedule_tasks = [
                ScheduleBoardTask(
                    board_id=board.id,
                    task_name=task.task_name,
                    task_status=task.task_status,
                )
                for task in request.schedule_board_tasks
            ]
            db.add_all(schedule_tasks)

        # detail: proceedings
        if request.proceedings_board_detail is not None:
            proceedings_detail = ProceedingsBoardDetail(
                board_id=board.id,
                meeting_date=request.proceedings_board_detail.meeting_date,
            )
            db.add(proceedings_detail)

            proceedings_detail_response = ResponseProceedingsBoardDetail(
                board_id=proceedings_detail.board_id,
                meeting_date=proceedings_detail.meeting_date,
            )

        # related users
        db.add_all(
            BoardAssignee(board_id=board.id, user_id=user_id)
            for user_id in request.assignee_user_ids # generator expression
        )
        db.add_all(
            BoardParticipant(board_id=board.id, user_id=user_id)
            for user_id in request.participant_user_ids
        )
        db.add_all(
            BoardCarbonCopy(board_id=board.id, user_id=user_id)
            for user_id in request.carbon_copy_user_ids
        )

        db.flush()

        # schedule task.id -> API response DTO
        schedule_task_responses = [
            ResponseScheduleBoardTaskDetail(
                id=task.id,
                task_name=task.task_name,
                task_status=task.task_status,
            )
            for task in schedule_tasks
        ]

        # DB model -> API response DTO
        response = BoardResponse(
            id=board.id,
            board_type=board.board_type,
            title=board.title,
            content=board.content,
            tag=board.tag,
            user_id=board.user_id,
            created_at=board.created_at,
            updated_at=board.updated_at,
            assignee_user_ids=request.assignee_user_ids,
            participant_user_ids=request.participant_user_ids,
            carbon_copy_user_ids=request.carbon_copy_user_ids,
            schedule_board_detail=schedule_detail_response,
            schedule_board_tasks=schedule_task_responses,
            proceedings_board_detail=proceedings_detail_response,
        )

        db.commit() # save transaction to DB
        return response
    except Exception:
        db.rollback() # rollback transaction
        raise # Re-raise the caught error
