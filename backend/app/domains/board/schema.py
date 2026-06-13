# Board API에서 주고받는 요청/응답 DTO를 정의하는 파일
# 클라이언트가 보내는 데이터와 서버가 반환하는 데이터의 형태를 작성

#  클라이언트가 보내는 JSON을 Python 객체처럼 다루게 도와주는 라이브러리
from pydantic import BaseModel, Field

from datetime import datetime

## create DTO
# detail boards
class CreateScheduleBoardDetail(BaseModel):
    start_at: datetime
    end_at: datetime
    importance: int = Field(ge=1, le=10) # 값 범위 검증
class CreateScheduleBoardTaskDetail(BaseModel):
    task_name: str
    task_status: int = Field(ge=1, le=4) # 값 범위 검증

class CreateProceedingsBoardDetail(BaseModel):
    meeting_date: datetime

## board
class CreateBoard(BaseModel):
    # BASIC_BOARD_TYPE = 1
    # SCHEDULE_BOARD_TYPE = 2
    # PROCEEDINGS_BOARD_TYPE = 3
    board_type: int = Field(1)
    title: str
    content: str
    tag: str | None = None
    user_id: int # JWT 구현 후 반드시 삭제

    # Save as empty list if not entered
    assignee_user_ids: list[int] = Field(default_factory=list)
    participant_user_ids: list[int] = Field(default_factory=list)
    carbon_copy_user_ids: list[int] = Field(default_factory=list)

    # connect detail by type
    # DTO for receiving detailed data by type nested within the request JSON
    # board_detail may or may not exist (if present, specify the format)
    schedule_board_detail: CreateScheduleBoardDetail | None = None # 2
    schedule_board_tasks: list[CreateScheduleBoardTaskDetail] = Field(default_factory=list)
    
    proceedings_board_detail: CreateProceedingsBoardDetail | None = None # 3


# UpdateBoard uses the same field structure as CreateBoard
class UpdateBoard(CreateBoard):
    pass


## read DTO
class BoardSearchParams(BaseModel):
    title: str | None = None
    user_id: int | None = None
    tag: str | None = None
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)


## response DTO

# detail boards
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
    user_id: int  # JWT 구현 후 반드시 삭제

    created_at: datetime
    updated_at: datetime

    assignee_user_ids: list[int] = Field(default_factory=list)
    participant_user_ids: list[int] = Field(default_factory=list)
    carbon_copy_user_ids: list[int] = Field(default_factory=list)

    schedule_board_detail: ResponseScheduleBoardDetail | None = None
    schedule_board_tasks: list[ResponseScheduleBoardTaskDetail] = Field(default_factory=list)

    proceedings_board_detail: ResponseProceedingsBoardDetail | None = None


class BoardPageResponse(BaseModel):
    items: list[BoardResponse]
    total: int
    page: int
    size: int
