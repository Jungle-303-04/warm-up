from __future__ import annotations

from datetime import datetime as DateTimeType
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    # 타입 힌트용 import다. 실행 중 순환 import를 피하려고 TYPE_CHECKING 안에서만 가져온다.
    from app.models.page import Page


class Tag(Base):
    # 페이지를 분류하거나 검색할 때 쓰는 태그 정보를 저장하는 테이블이다.
    __tablename__ = "tags"

    #고유 id
    # 태그 한 개를 구분하는 고유 번호다.
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    #태그의 이름
    # 태그 이름이다. 같은 이름의 태그가 여러 개 생기지 않도록 unique를 둔다.
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        # 태그 이름으로 검색하는 일이 많아서 인덱스를 둔다.
        index=True,
        nullable=False,
    )


