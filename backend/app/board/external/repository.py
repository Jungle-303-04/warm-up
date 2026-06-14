from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.board.api.schema import (
    BoardPageResponse,
    BoardResponse,
    BoardSearchParams,
    CreateBoard,
    ResponseProceedingsBoardDetail,
    ResponseScheduleBoardDetail,
    ResponseScheduleBoardTaskDetail,
    UpdateBoard,
)
from app.board.external.model import (
    Board,
    BoardAssignee,
    BoardCarbonCopy,
    BoardParticipant,
    ProceedingsBoardDetail,
    ScheduleBoardDetail,
    ScheduleBoardTask,
)
from app.db.transaction import db_transaction

RELATED_USER_MAPPINGS: tuple[tuple[type[Any], str], ...] = (
    (BoardAssignee, "assignee_user_ids"),
    (BoardParticipant, "participant_user_ids"),
    (BoardCarbonCopy, "carbon_copy_user_ids"),
)

DETAIL_MODELS: tuple[type[Any], ...] = (
    ScheduleBoardTask,
    ScheduleBoardDetail,
    ProceedingsBoardDetail,
)


class BoardSqlRepository:
    """BoardService가 SQLAlchemy 세부 쿼리를 몰라도 보드를 저장/조회하게 하는 구현체."""

    def insert(self, db: Session, request: CreateBoard) -> BoardResponse:
        return insert_board(db, request)

    def select_page(
        self,
        db: Session,
        search_params: BoardSearchParams,
    ) -> BoardPageResponse:
        return select_boards(db, search_params)

    def select_one(self, db: Session, board_id: int) -> BoardResponse | None:
        return select_board(db, board_id)

    def update(
        self,
        db: Session,
        board_id: int,
        request: UpdateBoard,
    ) -> BoardResponse | None:
        return update_board(db, board_id, request)

    def delete(self, db: Session, board_id: int) -> bool:
        return delete_board(db, board_id)


def insert_board(db: Session, request: CreateBoard) -> BoardResponse:
    """기본 보드, 타입별 상세, 관련 사용자를 하나의 트랜잭션으로 저장한다."""

    with db_transaction(db):
        board = build_board(request)
        db.add(board)
        db.flush()

        add_board_details(db, board.id, request)
        add_board_related_users(db, board.id, request)
        db.flush()

        return convert_to_board_response(db, board)


def select_boards(db: Session, search_params: BoardSearchParams) -> BoardPageResponse:
    """검색 조건과 페이지 정보를 SQL 쿼리로 바꿔 보드 목록 응답을 만든다."""

    filters = build_board_filters(search_params)
    query = apply_filters(select(Board), filters)
    count_query = apply_filters(select(func.count()).select_from(Board), filters)
    offset = (search_params.page - 1) * search_params.size

    boards = db.scalars(
        query.order_by(Board.id).offset(offset).limit(search_params.size)
    ).all()

    return BoardPageResponse(
        items=[convert_to_board_response(db, board) for board in boards],
        total=db.scalar(count_query) or 0,
        page=search_params.page,
        size=search_params.size,
    )


def select_board(db: Session, board_id: int) -> BoardResponse | None:
    """단건 조회 결과가 없으면 서비스가 404로 바꿀 수 있게 None을 반환한다."""

    board = db.get(Board, board_id)
    if board is None:
        return None
    return convert_to_board_response(db, board)


def update_board(db: Session, board_id: int, request: UpdateBoard) -> BoardResponse | None:
    """보드 본문과 타입별 상세를 요청 내용 기준으로 완전히 교체한다."""

    with db_transaction(db):
        board = db.get(Board, board_id)
        if board is None:
            return None

        update_board_fields(board, request)
        delete_board_details(db, board_id)
        delete_board_related_users(db, board_id)
        add_board_details(db, board_id, request)
        add_board_related_users(db, board_id, request)
        db.flush()

        return convert_to_board_response(db, board)


def delete_board(db: Session, board_id: int) -> bool:
    """자식 테이블을 먼저 정리한 뒤 부모 보드를 삭제해 FK 오류를 피한다."""

    with db_transaction(db):
        board = db.get(Board, board_id)
        if board is None:
            return False

        delete_board_details(db, board_id)
        delete_board_related_users(db, board_id)
        db.delete(board)
        return True


def convert_to_board_response(db: Session, board: Board) -> BoardResponse:
    """분리된 보드 테이블들을 프론트가 쓰는 단일 응답 DTO로 조립한다."""

    return BoardResponse(
        id=board.id,
        board_type=board.board_type,
        title=board.title,
        content=board.content,
        tag=board.tag,
        user_id=board.user_id,
        created_at=board.created_at,
        updated_at=board.updated_at,
        assignee_user_ids=select_related_user_ids(db, BoardAssignee, board.id),
        participant_user_ids=select_related_user_ids(db, BoardParticipant, board.id),
        carbon_copy_user_ids=select_related_user_ids(db, BoardCarbonCopy, board.id),
        schedule_board_detail=select_schedule_detail(db, board.id),
        schedule_board_tasks=select_schedule_tasks(db, board.id),
        proceedings_board_detail=select_proceedings_detail(db, board.id),
    )


def build_board(request: CreateBoard | UpdateBoard) -> Board:
    """생성/수정 요청에서 모든 보드 타입이 공통으로 갖는 기본 컬럼만 모델로 만든다."""

    return Board(
        board_type=request.board_type,
        title=request.title,
        content=request.content,
        tag=request.tag,
        user_id=request.user_id,
    )


def update_board_fields(board: Board, request: CreateBoard | UpdateBoard) -> None:
    """이미 존재하는 보드 행의 공통 컬럼을 요청 값으로 갱신한다."""

    board.board_type = request.board_type
    board.title = request.title
    board.content = request.content
    board.tag = request.tag
    board.user_id = request.user_id


def build_board_filters(search_params: BoardSearchParams) -> list[Any]:
    """선택적으로 들어온 검색 조건만 SQLAlchemy where 조건으로 변환한다."""

    filters: list[Any] = []
    if search_params.title is not None:
        filters.append(Board.title.ilike(f"%{search_params.title}%"))
    if search_params.user_id is not None:
        filters.append(Board.user_id == search_params.user_id)
    if search_params.tag is not None:
        filters.append(Board.tag == search_params.tag)
    return filters


def apply_filters(query, filters: list[Any]):
    """목록 쿼리와 count 쿼리에 같은 검색 조건을 재사용한다."""

    if not filters:
        return query
    return query.where(*filters)


def add_board_details(
    db: Session,
    board_id: int,
    request: CreateBoard | UpdateBoard,
) -> None:
    """board_type에 따라 별도 테이블에 저장되는 상세 정보를 추가한다."""

    if request.schedule_board_detail is not None:
        db.add(
            ScheduleBoardDetail(
                board_id=board_id,
                start_at=request.schedule_board_detail.start_at,
                end_at=request.schedule_board_detail.end_at,
                importance=request.schedule_board_detail.importance,
            )
        )
        db.add_all(
            ScheduleBoardTask(
                board_id=board_id,
                task_name=task.task_name,
                task_status=task.task_status,
            )
            for task in request.schedule_board_tasks
        )

    if request.proceedings_board_detail is not None:
        db.add(
            ProceedingsBoardDetail(
                board_id=board_id,
                meeting_date=request.proceedings_board_detail.meeting_date,
            )
        )


def add_board_related_users(
    db: Session,
    board_id: int,
    request: CreateBoard | UpdateBoard,
) -> None:
    """담당자, 참여자, 참조자 매핑을 같은 규칙으로 저장한다."""

    for model, field_name in RELATED_USER_MAPPINGS:
        db.add_all(
            model(board_id=board_id, user_id=user_id)
            for user_id in getattr(request, field_name)
        )


def delete_board_details(db: Session, board_id: int) -> None:
    """보드 타입 변경이나 삭제 전에 기존 상세 테이블 데이터를 정리한다."""

    for model in DETAIL_MODELS:
        delete_rows_by_board_id(db, model, board_id)


def delete_board_related_users(db: Session, board_id: int) -> None:
    """보드와 사용자 사이의 모든 역할 매핑을 한 번에 정리한다."""

    for model, _ in RELATED_USER_MAPPINGS:
        delete_rows_by_board_id(db, model, board_id)


def delete_rows_by_board_id(db: Session, model: type[Any], board_id: int) -> None:
    """board_id를 가진 단순 자식 테이블 삭제 패턴을 공통화한다."""

    db.query(model).filter(model.board_id == board_id).delete()


def select_related_user_ids(
    db: Session,
    model: type[Any],
    board_id: int,
) -> list[int]:
    """역할별 매핑 테이블에서 프론트 응답에 필요한 user_id 목록만 꺼낸다."""

    return db.scalars(
        select(model.user_id).where(model.board_id == board_id)
    ).all()


def select_schedule_detail(
    db: Session,
    board_id: int,
) -> ResponseScheduleBoardDetail | None:
    """일정 상세가 있는 보드만 일정 응답 DTO를 포함하게 한다."""

    detail = db.get(ScheduleBoardDetail, board_id)
    if detail is None:
        return None
    return ResponseScheduleBoardDetail(
        board_id=detail.board_id,
        start_at=detail.start_at,
        end_at=detail.end_at,
        importance=detail.importance,
    )


def select_schedule_tasks(
    db: Session,
    board_id: int,
) -> list[ResponseScheduleBoardTaskDetail] | None:
    """일정 보드가 아닐 때는 tasks를 None으로 유지해 보드 타입 차이를 드러낸다."""

    if db.get(ScheduleBoardDetail, board_id) is None:
        return None

    tasks = db.scalars(
        select(ScheduleBoardTask)
        .where(ScheduleBoardTask.board_id == board_id)
        .order_by(ScheduleBoardTask.id)
    ).all()
    return [
        ResponseScheduleBoardTaskDetail(
            id=task.id,
            task_name=task.task_name,
            task_status=task.task_status,
        )
        for task in tasks
    ]


def select_proceedings_detail(
    db: Session,
    board_id: int,
) -> ResponseProceedingsBoardDetail | None:
    """회의록 상세가 있는 보드만 회의 응답 DTO를 포함하게 한다."""

    detail = db.get(ProceedingsBoardDetail, board_id)
    if detail is None:
        return None
    return ResponseProceedingsBoardDetail(
        board_id=detail.board_id,
        meeting_date=detail.meeting_date,
    )
