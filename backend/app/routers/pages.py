from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, distinct, func, or_, select #파이썬 코드로 db 다루게 해준다
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.page import Page
from app.models.page_block import PageBlock
from app.models.tag import Tag
from app.models.user import User
from app.schemas.page_schema import (
    CalendarPageItem,
    PageCreate,
    PageListResponse,
    PageResponse,
    PageUpdate,
)
from app.models.enums import PageType


router = APIRouter(prefix="/pages", tags=["Pages"])


@router.post(
    "",
    response_model=PageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_page(
    payload : PageCreate, #클라가 보낸 JSON을 PageCreate 객체로 변환,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    page = Page(
        type = payload.type,
        title = payload.title,
        date = payload.date,
        start_time = payload.start_time,
        end_time = payload.end_time,
        author_id = current_user.id,
        participants = payload.participants,
        tag = payload.tag,
    )


    for index, block in enumerate(payload.blocks):
        page.blocks.append(
           PageBlock(
            type = block.type,
            content = block.content,
            checked = block.checked,
            order_index = index
        )
    )
    db.add(page) #page 객체를 db에 저장할 예정
    db.commit() #db 저장
    db.refresh(page)

    return page

@router.get(
    "",
    response_model = PageListResponse,
)
def get_pages(
    type_: PageType | None = Query(default=None, alias= "type"), #회의, 회고 필터

)
