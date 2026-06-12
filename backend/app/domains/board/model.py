# Board 테이블과 연결되는 SQLAlchemy 모델을 정의하는 파일
# DB에 저장되는 보드 객체의 컬럼과 관계 작성
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin

BASIC_BOARD_TYPE = 1
SCHEDULE_BOARD_TYPE = 2
PROCEEDINGS_BOARD_TYPE = 3
class Board(Base, IdMixin, TimestampMixin):
    __tablename__ = "board"

    # BASIC_BOARD_TYPE = 1
    # SCHEDULE_BOARD_TYPE = 2
    # PROCEEDINGS_BOARD_TYPE = 3
    board_type: Mapped[int] = mapped_column(Integer, nullable=False)

    title: Mapped[str] = mapped_column(String, nullable = False,)
    content: Mapped[str] = mapped_column(Text, nullable = False,)
    tag: Mapped[str | None] = mapped_column(String, nullable = True,)

    # Foreignkey
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id"),
        nullable = False,
    )


class ScheduleBoardDetail(Base): # 2
    __tablename__ = "schedule_board_detail"

    # Apply constraints to the values ​​stored in the DB table
    __table_args__ = (
        CheckConstraint(
            "importance >= 1 AND importance <= 10",
            name = "check_schedule_board_importance_range",
        ),
    )

    # Foreignkey
    board_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("board.id"),
        primary_key = True,
        nullable = False,
    )
    
    start_at: Mapped[datetime] = mapped_column(
        DateTime,
        default = datetime.utcnow,
        nullable = False,
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime,
        default = datetime.utcnow,
        nullable = False,
    )

    importance: Mapped[int] = mapped_column(
        Integer,
        nullable = False,
    )

class ScheduleBoardTask(Base, IdMixin):
    __tablename__ = "schedule_board_task"

    __table_args__ = (
        CheckConstraint(
            "task_status >= 1 AND task_status <= 4",
            name="check_schedule_task_status_range",
        ),
    )

    # Foreignkey
    board_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("schedule_board_detail.board_id"),
        primary_key = False,
        nullable = False,
    )

    task_name: Mapped[str] = mapped_column(String, nullable = False,)
    
    # 1: Todo, 2: In_progress, 3: Done, 4: Blocked 
    task_status: Mapped[int] = mapped_column(Integer, nullable = False,)


class ProceedingsBoardDetail(Base): #3
    __tablename__ = "proceedings_board_detail"

    # Foreignkey
    board_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("board.id"),
        primary_key = True,
        nullable = False,)
    
    meeting_date: Mapped[datetime] = mapped_column(
        DateTime,
        default = datetime.utcnow,
        nullable = False,
    )



## partner
class BoardCarbonCopy(Base): # 참조인
    __tablename__ = "board_carbon_copy"
    # Foreignkey
    board_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("board.id"),
        primary_key = True, # composite primary key
        nullable = False,)

    # Foreignkey
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id"),
        primary_key = True, # composite primary key
        nullable = False,
    )

class BoardAssignee(Base): # 담당자 
    __tablename__ = "board_assignee"
    # Foreignkey
    board_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("board.id"),
        primary_key = True, # composite primary key
        nullable = False,)

    # Foreignkey
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id"),
        primary_key = True, # composite primary key
        nullable = False,
    )

class BoardParticipant(Base): # 참여자 
    __tablename__ = "board_participant"
    # Foreignkey
    board_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("board.id"),
        primary_key = True, # composite primary key
        nullable = False,)

    # Foreignkey
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id"),
        primary_key = True, # composite primary key
        nullable = False,
    )