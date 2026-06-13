# Board 데이터의 DB 접근 로직을 작성하는 파일
# SQLAlchemy를 사용한 조회, 생성, 수정, 삭제 쿼리 작성
from sqlalchemy import func, select
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
    BoardPageResponse,
    BoardSearchParams,
    ResponseProceedingsBoardDetail,
    ResponseScheduleBoardDetail,
    ResponseScheduleBoardTaskDetail,
    UpdateBoard,
)


def convert_to_board_response(db: Session, board: Board) -> BoardResponse:
    # collect detail data for API response
    schedule_detail = db.get(ScheduleBoardDetail, board.id)
    proceedings_detail = db.get(ProceedingsBoardDetail, board.id)

    schedule_tasks = db.scalars(
        select(ScheduleBoardTask).where(ScheduleBoardTask.board_id == board.id)
    ).all()
    assignee_user_ids = db.scalars(
        select(BoardAssignee.user_id).where(BoardAssignee.board_id == board.id)
    ).all()
    participant_user_ids = db.scalars(
        select(BoardParticipant.user_id).where(BoardParticipant.board_id == board.id)
    ).all()
    carbon_copy_user_ids = db.scalars(
        select(BoardCarbonCopy.user_id).where(BoardCarbonCopy.board_id == board.id)
    ).all()

    schedule_detail_response = None
    if schedule_detail is not None:
        schedule_detail_response = ResponseScheduleBoardDetail(
            board_id=schedule_detail.board_id,
            start_at=schedule_detail.start_at,
            end_at=schedule_detail.end_at,
            importance=schedule_detail.importance,
        )

    proceedings_detail_response = None
    if proceedings_detail is not None:
        proceedings_detail_response = ResponseProceedingsBoardDetail(
            board_id=proceedings_detail.board_id,
            meeting_date=proceedings_detail.meeting_date,
        )

    schedule_task_responses = [
        ResponseScheduleBoardTaskDetail(
            id=task.id,
            task_name=task.task_name,
            task_status=task.task_status,
        )
        for task in schedule_tasks
    ]

    return BoardResponse(
        id=board.id,
        board_type=board.board_type,
        title=board.title,
        content=board.content,
        tag=board.tag,
        user_id=board.user_id,
        created_at=board.created_at,
        updated_at=board.updated_at,
        assignee_user_ids=assignee_user_ids,
        participant_user_ids=participant_user_ids,
        carbon_copy_user_ids=carbon_copy_user_ids,
        schedule_board_detail=schedule_detail_response,
        schedule_board_tasks=schedule_task_responses,
        proceedings_board_detail=proceedings_detail_response,
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


def select_boards(db: Session, search_params: BoardSearchParams) -> BoardPageResponse:
    # read boards by search conditions
    filters = []

    if search_params.title is not None:
        filters.append(Board.title.ilike(f"%{search_params.title}%"))
    if search_params.user_id is not None:
        filters.append(Board.user_id == search_params.user_id)
    if search_params.tag is not None:
        filters.append(Board.tag == search_params.tag)

    query = select(Board)
    count_query = select(func.count()).select_from(Board)

    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)

    offset = (search_params.page - 1) * search_params.size
    total = db.scalar(count_query) or 0
    boards = db.scalars(
        query.order_by(Board.id).offset(offset).limit(search_params.size)
    ).all()

    return BoardPageResponse(
        items=[convert_to_board_response(db, board) for board in boards],
        total=total,
        page=search_params.page,
        size=search_params.size,
    )


def select_board(db: Session, board_id: int) -> BoardResponse | None:
    # read board by id
    board = db.get(Board, board_id)

    if board is None:
        return None

    return convert_to_board_response(db, board)


def update_board(db: Session, board_id: int, request: UpdateBoard) -> BoardResponse | None:
    try:
        # read board before update
        board = db.get(Board, board_id)

        if board is None:
            return None

        # common board data
        board.board_type = request.board_type
        board.title = request.title
        board.content = request.content
        board.tag = request.tag
        board.user_id = request.user_id

        # delete old type-specific detail data
        delete_board_details(db, board_id)

        # create new type-specific detail data
        if request.schedule_board_detail is not None:
            db.add(
                ScheduleBoardDetail(
                    board_id=board.id,
                    start_at=request.schedule_board_detail.start_at,
                    end_at=request.schedule_board_detail.end_at,
                    importance=request.schedule_board_detail.importance,
                )
            )

            schedule_tasks = [
                ScheduleBoardTask(
                    board_id=board.id,
                    task_name=task.task_name,
                    task_status=task.task_status,
                )
                for task in request.schedule_board_tasks
            ]
            db.add_all(schedule_tasks)

        if request.proceedings_board_detail is not None:
            db.add(
                ProceedingsBoardDetail(
                    board_id=board.id,
                    meeting_date=request.proceedings_board_detail.meeting_date,
                )
            )

        # replace related users
        delete_board_related_users(db, board_id)
        add_board_related_users(db, board_id, request)

        db.flush()
        response = convert_to_board_response(db, board)
        db.commit()
        return response
    except Exception:
        db.rollback()
        raise


def delete_board(db: Session, board_id: int) -> bool:
    try:
        # read board before delete
        board = db.get(Board, board_id)

        if board is None:
            return False

        delete_board_details(db, board_id)
        delete_board_related_users(db, board_id)

        db.delete(board)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


def delete_board_details(db: Session, board_id: int) -> None:
    # delete child tables before parent detail tables
    db.query(ScheduleBoardTask).filter(ScheduleBoardTask.board_id == board_id).delete()
    db.query(ScheduleBoardDetail).filter(ScheduleBoardDetail.board_id == board_id).delete()
    db.query(ProceedingsBoardDetail).filter(ProceedingsBoardDetail.board_id == board_id).delete()


def delete_board_related_users(db: Session, board_id: int) -> None:
    # delete related user mappings
    db.query(BoardAssignee).filter(BoardAssignee.board_id == board_id).delete()
    db.query(BoardParticipant).filter(BoardParticipant.board_id == board_id).delete()
    db.query(BoardCarbonCopy).filter(BoardCarbonCopy.board_id == board_id).delete()


def add_board_related_users(db: Session, board_id: int, request: CreateBoard | UpdateBoard) -> None:
    # add related user mappings
    db.add_all(
        BoardAssignee(board_id=board_id, user_id=user_id)
        for user_id in request.assignee_user_ids
    )
    db.add_all(
        BoardParticipant(board_id=board_id, user_id=user_id)
        for user_id in request.participant_user_ids
    )
    db.add_all(
        BoardCarbonCopy(board_id=board_id, user_id=user_id)
        for user_id in request.carbon_copy_user_ids
    )
