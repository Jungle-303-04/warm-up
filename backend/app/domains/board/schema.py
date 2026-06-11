# Board API에서 주고받는 요청/응답 DTO를 정의하는 파일
# 클라이언트가 보내는 데이터와 서버가 반환하는 데이터의 형태를 작성

#  클라이언트가 보내는 JSON을 Python 객체처럼 다루게 도와주는 라이브러리
from pydantic import BaseModel, Field

from datetime import datetime

## detail boards
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
    # 1: ScheduleBoardDetail
    # 2: ProceedingsBoardDetail
    # 3:
    # 4:
    board_type: int
    title: str
    content: str
    tag: str | None = None
    user_id: int # JWT 구현 후 반드시 삭제

    # 미입력시, 빈리스트로 저장
    assignee_user_ids: list[int] = Field(default_factory=list)
    participant_user_ids: list[int] = Field(default_factory=list)
    carbon_copy_user_ids: list[int] = Field(default_factory=list)

    # 타입별 detail 연결
    # 요청 JSON 안에 타입별 상세 데이터를 중첩해서 받기 위한 DTO 구조

    # board_detail이라는 필드가 있을수도(있다면 형태 지정) 없을수도 있음.
    schedule_board_detail: CreateScheduleBoardDetail | None = None # 1
    schedule_board_tasks: list[CreateScheduleBoardTaskDetail] = Field(default_factory=list)
    
    proceedings_board_detail: CreateProceedingsBoardDetail | None = None # 2
