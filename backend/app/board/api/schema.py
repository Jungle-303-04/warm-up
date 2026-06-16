from datetime import datetime

from pydantic import BaseModel, Field


class CreateScheduleBoardDetail(BaseModel):
    start_at: datetime
    end_at: datetime
    importance: int = Field(ge=1, le=10)


class CreateScheduleBoardTaskDetail(BaseModel):
    task_name: str
    task_status: int = Field(ge=1, le=4)


class CreateProceedingsBoardDetail(BaseModel):
    meeting_date: datetime


class CreateBoard(BaseModel):
    board_type: int = Field(1)
    title: str
    content: str
    tag: str | None = None
    user_id: int | None = None

    assignee_user_ids: list[int] = Field(default_factory=list)
    participant_user_ids: list[int] = Field(default_factory=list)
    carbon_copy_user_ids: list[int] = Field(default_factory=list)

    schedule_board_detail: CreateScheduleBoardDetail | None = None
    schedule_board_tasks: list[CreateScheduleBoardTaskDetail] = Field(default_factory=list)
    proceedings_board_detail: CreateProceedingsBoardDetail | None = None


class UpdateBoard(CreateBoard):
    pass


class BoardSearchParams(BaseModel):
    title: str | None = None
    user_id: int | None = None
    tag: str | None = None
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)


class ResponseScheduleBoardDetail(BaseModel):
    board_id: int
    start_at: datetime
    end_at: datetime
    importance: int


class ResponseScheduleBoardTaskDetail(BaseModel):
    id: int
    task_name: str
    task_status: int


class ResponseProceedingsBoardDetail(BaseModel):
    board_id: int
    meeting_date: datetime


class BoardResponse(BaseModel):
    id: int
    board_type: int
    title: str
    content: str
    tag: str | None = None
    user_id: int
    created_at: datetime
    updated_at: datetime

    assignee_user_ids: list[int] = Field(default_factory=list)
    participant_user_ids: list[int] = Field(default_factory=list)
    carbon_copy_user_ids: list[int] = Field(default_factory=list)

    schedule_board_detail: ResponseScheduleBoardDetail | None = None
    schedule_board_tasks: list[ResponseScheduleBoardTaskDetail] | None = None
    proceedings_board_detail: ResponseProceedingsBoardDetail | None = None


class BoardPageResponse(BaseModel):
    items: list[BoardResponse]
    total: int
    page: int
    size: int
