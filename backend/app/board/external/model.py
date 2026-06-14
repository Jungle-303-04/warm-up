from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin

BASIC_BOARD_TYPE = 1
SCHEDULE_BOARD_TYPE = 2
PROCEEDINGS_BOARD_TYPE = 3


class Board(Base, IdMixin, TimestampMixin):
    __tablename__ = "board"

    board_type: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tag: Mapped[str | None] = mapped_column(String, nullable=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id"),
        nullable=False,
    )


class ScheduleBoardDetail(Base):
    __tablename__ = "schedule_board_detail"
    __table_args__ = (
        CheckConstraint(
            "importance >= 1 AND importance <= 10",
            name="check_schedule_board_importance_range",
        ),
    )

    board_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("board.id"),
        primary_key=True,
        nullable=False,
    )
    start_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    importance: Mapped[int] = mapped_column(Integer, nullable=False)


class ScheduleBoardTask(Base, IdMixin):
    __tablename__ = "schedule_board_task"
    __table_args__ = (
        CheckConstraint(
            "task_status >= 1 AND task_status <= 4",
            name="check_schedule_task_status_range",
        ),
    )

    board_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("schedule_board_detail.board_id"),
        nullable=False,
    )
    task_name: Mapped[str] = mapped_column(String, nullable=False)
    task_status: Mapped[int] = mapped_column(Integer, nullable=False)


class ProceedingsBoardDetail(Base):
    __tablename__ = "proceedings_board_detail"

    board_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("board.id"),
        primary_key=True,
        nullable=False,
    )
    meeting_date: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class BoardCarbonCopy(Base):
    __tablename__ = "board_carbon_copy"

    board_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("board.id"),
        primary_key=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id"),
        primary_key=True,
        nullable=False,
    )


class BoardAssignee(Base):
    __tablename__ = "board_assignee"

    board_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("board.id"),
        primary_key=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id"),
        primary_key=True,
        nullable=False,
    )


class BoardParticipant(Base):
    __tablename__ = "board_participant"

    board_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("board.id"),
        primary_key=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id"),
        primary_key=True,
        nullable=False,
    )
