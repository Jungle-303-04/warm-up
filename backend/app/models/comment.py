from __future__ import annotations

from datetime import datetime as DateTimeType
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    # 타입 힌트용 import다. 실행 중 순환 import를 피하려고 TYPE_CHECKING 안에서만 가져온다.
    from app.models.page import Page
    from app.models.user import User


class Comment(Base):
    # 댓글 정보를 저장하는 테이블이다.
    __tablename__ = "comments"

    #고유 id
    # 댓글 한 개를 구분하는 고유 번호다.
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    #
    # 이 댓글이 어느 페이지에 달렸는지 저장한다.
    page_id: Mapped[int] = mapped_column(
        ForeignKey("pages.id", ondelete="CASCADE"), #페이지 삭제되면 이 댓글도 같이 삭제 
        nullable=False,
        # 페이지별 댓글 목록 조회가 많아서 인덱스를 둔다.
        index=True,
    )

    # 이 댓글을 작성한 사용자의 id다.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),#유저 삭제되면 유저 댓글 삭제
        nullable=False,
        # 사용자별 댓글 조회가 필요할 수 있어서 인덱스를 둔다.
        index=True,
    )

    #댓글 내용
    # 댓글 본문은 길어질 수 있으므로 Text 타입으로 저장한다.
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    #댓글 생성 일시
    # 댓글이 작성된 시각이다. DB 서버 시간이 자동으로 들어간다.
    created_at: Mapped[DateTimeType] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    #page_id보고 comment.page 쓸수 있게 해줌
    # page_id를 보고 연결된 Page 객체를 바로 사용할 수 있게 한다. 예: comment.page.title
    page: Mapped["Page"] = relationship(
        back_populates="comments",
    )

    #user_id보고 comment.author 쓸 수 있게 해줌
    # user_id를 보고 댓글 작성자 User 객체를 바로 사용할 수 있게 한다. 예: comment.author.nickname
    author: Mapped["User"] = relationship(
        back_populates="comments",
    )
