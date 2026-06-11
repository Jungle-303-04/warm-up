from __future__ import annotations

from datetime import datetime as DateTimeType
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    # 타입 힌트용 import다. 실행 중 순환 import를 피하려고 TYPE_CHECKING 안에서만 가져온다.
    from app.models.comment import Comment
    from app.models.page import Page

class User(Base):
    # 서비스 사용자 계정 정보를 저장하는 테이블이다.
    __tablename__ = "users"

    # 사용자 한 명을 구분하는 고유 번호다.
    id : Mapped[int] = mapped_column(primary_key = True, index = True)

    # 로그인과 계정 식별에 쓰는 이메일이다. 같은 이메일로 중복 가입하지 못하게 한다.
    email : Mapped[str] = mapped_column(
        String(255),
        unique = True, # 중복방지
        index = True,
        nullable = False,
    )

    # 비밀번호 원문이 아니라 해시된 값을 저장한다.
    password_hash : Mapped[str] = mapped_column(
        String(255),
        nullable = False,
    )

    # 화면에 보여줄 사용자 이름이다. 현재 설계에서는 중복을 막기 위해 unique를 둔다.
    nickname : Mapped[str] = mapped_column(
        String(50),
        nullable = False,
        unique = True,   
    )

    # 사용자가 가입한 시각이다. DB 서버 시간이 자동으로 들어간다.
    created_at: Mapped[DateTimeType] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(), #현재 시간 넣어준다
        nullable = False,
    )

    #유저 한명은 여러개의 page를 작성할 수 있다
    pages : Mapped[list["Page"]] = relationship( #테이블 사이의 관계
        # User.pages와 Page.author를 서로 연결한다.
        back_populates = "author",
        cascade = "all, delete-orphan"
    )

    # 이 사용자가 작성한 댓글 목록이다. User 1명은 여러 Comment를 작성할 수 있다.
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
    )
