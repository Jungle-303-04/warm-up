from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.enums import PageType
from app.models.page import Page
from app.models.page_block import PageBlock
from app.models.user import User
from app.schemas.page_schema import (
    CalendarPageItem,
    PageCreate,
    PageListResponse,
    PageResponse,
    PageUpdate,
)

# Page 관련 API를 /pages 경로 아래에 묶는다.
router = APIRouter(prefix="/pages", tags=["Pages"])


def get_page_or_404(
    db: Session,
    page_id: int,
) -> Page:
    # page_id에 해당하는 Page를 찾고, 본문 블록도 함께 불러온다.
    page = db.execute(
        select(Page)
        .options(
            selectinload(Page.blocks),
        )
        .where(Page.id == page_id)
    ).scalar_one_or_none()

    if page is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="페이지를 찾을 수 없습니다.",
        )

    return page


def check_page_owner(
    page: Page,
    current_user: User,
):
    # 현재 로그인한 사용자가 이 Page의 작성자인지 확인한다.
    if page.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 페이지에 접근할 권한이 없습니다.",
        )


@router.post(
    "",
    response_model=PageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_page(
    payload: PageCreate,  # 클라이언트가 보낸 페이지 생성 데이터
    db: Session = Depends(get_db),  # DB 작업에 사용할 세션
    current_user: User = Depends(get_current_user),  # 토큰으로 확인한 현재 사용자
):
    # 회의/회고 구분은 payload.type에 저장된다.
    page = Page(
        type=payload.type,
        title=payload.title,
        date=payload.date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        author_id=current_user.id,
        participants=payload.participants,
    )

    # 먼저 Page를 DB 세션에 추가하고 id를 받아온다.
    db.add(page)
    db.flush()

    # payload.blocks에 들어온 본문 블록들을 PageBlock으로 저장한다.
    for index, block in enumerate(payload.blocks):
        page_block = PageBlock(
            page_id=page.id,
            type=block.type,
            content=block.content,
            checked=block.checked,
            order_index=index,
        )
        db.add(page_block)

    db.commit()

    # 저장된 Page를 다시 조회해서 blocks까지 포함된 응답으로 반환한다.
    return get_page_or_404(db, page.id)


# 페이지 목록 조회 API
# 예: GET /pages?type=MEETING&page=1&size=10
@router.get(
    "",
    response_model=PageListResponse,
)
def get_pages(
    type_: PageType | None = Query(default=None, alias="type"),  # MEETING 또는 RETROSPECTIVE
    page: int = Query(default=1, ge=1),  # 조회할 페이지 번호
    size: int = Query(default=10, ge=1, le=100),  # 한 번에 가져올 개수
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Page 목록을 날짜 최신순, 생성시간 최신순으로 조회한다.
    stmt = select(Page).order_by(Page.date.desc(), Page.created_at.desc())

    # 전체 Page 개수를 센다.
    count_stmt = select(func.count(Page.id))

    # type이 들어오면 회의 또는 회고만 필터링한다.
    if type_ is not None:
        stmt = stmt.where(Page.type == type_)
        count_stmt = count_stmt.where(Page.type == type_)

    total = db.execute(count_stmt).scalar_one()

    # 페이지네이션을 적용해서 현재 페이지에 보여줄 데이터만 가져온다.
    items = db.execute(
        stmt.offset((page - 1) * size).limit(size)
    ).scalars().all()

    return PageListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


# 캘린더 화면에서 특정 연/월에 해당하는 Page 목록을 조회하는 API
@router.get(
    "/calendar",
    response_model=list[CalendarPageItem],
)
def get_calendar_pages(
    # year와 month는 URL 쿼리 파라미터로 받는다.
    # 예: /pages/calendar?year=2026&month=6
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 조회할 달의 시작일을 만든다.
    start_date = date(year, month, 1)

    # 다음 달 1일을 end_date로 잡고, end_date 미만 조건으로 해당 월만 조회한다.
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    # 현재 로그인한 사용자의 Page 중 해당 월에 속한 것만 가져온다.
    items = db.execute(
        select(Page)
        .where(Page.author_id == current_user.id)
        .where(Page.date >= start_date)
        .where(Page.date < end_date)
        .order_by(Page.date.asc(), Page.start_time.asc())
    ).scalars().all()

    # FastAPI가 CalendarPageItem 리스트 형태의 JSON으로 변환해서 응답한다.
    return items


# 검색 API 초안이다. 현재는 사용하지 않으므로 주석 처리해 두었다.
# @router.get(
#     "/search",
#     response_model=PageListResponse,
# )
# def search_pages(
#     keyword: str = Query(..., min_length=1),
#     page: int = Query(default=1, ge=1),
#     size: int = Query(default=10, ge=1, le=100),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     pattern = f"%{keyword}%"
#
#     # 제목이나 본문 블록 내용에 검색어가 포함된 Page를 찾는다.
#     base_filter = or_(
#         Page.title.ilike(pattern),
#         PageBlock.content.ilike(pattern),
#     )
#
#     # 검색 조건에 맞는 Page 개수를 센다.
#     total = db.execute(
#         select(func.count(distinct(Page.id)))
#         .outerjoin(PageBlock, Page.id == PageBlock.page_id)
#         .where(base_filter)
#     ).scalar_one()
#
#     # 검색 결과를 페이지네이션해서 가져온다.
#     items = db.execute(
#         select(Page)
#         .outerjoin(PageBlock, Page.id == PageBlock.page_id)
#         .where(base_filter)
#         .distinct()
#         .order_by(Page.date.desc(), Page.created_at.desc())
#         .offset((page - 1) * size)
#         .limit(size)
#     ).scalars().all()
#
#     return PageListResponse(
#         items=items,
#         total=total,
#         page=page,
#         size=size,
#     )


# 특정 Page 하나의 상세 정보를 가져온다.
@router.get(
    "/{page_id}",
    response_model=PageResponse,
)
def get_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_page_or_404(db, page_id)


@router.patch(
    "/{page_id}",
    response_model=PageResponse,
)
def update_page(
    page_id: int,
    payload: PageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 수정할 Page를 찾고, 현재 사용자가 작성자인지 확인한다.
    page = get_page_or_404(db, page_id)
    check_page_owner(page, current_user)

    # payload에 들어온 값만 선택적으로 수정한다.
    if payload.title is not None:
        page.title = payload.title

    if payload.date is not None:
        page.date = payload.date

    if payload.start_time is not None:
        page.start_time = payload.start_time

    if payload.end_time is not None:
        page.end_time = payload.end_time

    if payload.participants is not None:
        page.participants = payload.participants

    if payload.ai_summary is not None:
        page.ai_summary = payload.ai_summary

    # blocks가 전달되면 기존 블록을 삭제하고 새 블록 목록으로 다시 저장한다.
    if payload.blocks is not None:
        db.execute(
            delete(PageBlock).where(PageBlock.page_id == page.id)
        )
        db.flush()

        for index, block in enumerate(payload.blocks):
            db.add(
                PageBlock(
                    page_id=page.id,
                    type=block.type,
                    content=block.content,
                    checked=block.checked,
                    order_index=index,
                )
            )

    db.commit()

    return get_page_or_404(db, page.id)


@router.delete(
    "/{page_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 삭제할 Page를 찾고, 현재 사용자가 작성자인지 확인한 뒤 삭제한다.
    page = get_page_or_404(db, page_id)
    check_page_owner(page, current_user)

    db.delete(page)
    db.commit()

    return None
