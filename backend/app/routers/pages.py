from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, distinct, func, or_, select
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

# router 생성
router = APIRouter(prefix="/pages", tags=["Pages"])


# 사용자가 보낸 태그 이름들을 깔끔하게 정리
def normalize_tag_names(tag_names: list[str]) -> list[str]:
    result = []
    seen = set()

    for name in tag_names:
        clean_name = name.strip() #공백 제거

        if not clean_name: #빈 문자열 버린다
            continue

        key = clean_name.lower() #소문자로 바꾼다

        if key in seen: #이미 본 태그면
            continue

        seen.add(key) 
        result.append(clean_name) # 정리된 태그 이름 결과 리스트에 추가

    return result #결과 리스트 반환


def get_or_create_tags(
    db: Session,
    tag_names: list[str],
) -> list[Tag]:
    normalized_names = normalize_tag_names(tag_names)

    if not normalized_names:
        return []

    existing_tags = db.execute(
        select(Tag).where(Tag.name.in_(normalized_names))
    ).scalars().all()

    existing_by_name = {tag.name: tag for tag in existing_tags}

    tags: list[Tag] = []

    for name in normalized_names:
        if name in existing_by_name:
            tags.append(existing_by_name[name])
            continue

        tag = Tag(name=name)
        db.add(tag)
        db.flush()
        tags.append(tag)

    return tags


def get_page_or_404(
    db: Session,
    page_id: int,
) -> Page:
    page = db.execute(
        select(Page)
        .options(
            selectinload(Page.blocks),
            selectinload(Page.tags),
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
    if page.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 페이지를 수정하거나 삭제할 권한이 없습니다.",
        )


@router.post(
    "",
    response_model=PageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_page(
    payload: PageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    page = Page(
        type=payload.type,
        title=payload.title,
        date=payload.date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        author_id=current_user.id,
        participants=payload.participants,
    )

    page.tags = get_or_create_tags(db, payload.tags)

    db.add(page)
    db.flush()

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

    return get_page_or_404(db, page.id)


@router.get(
    "",
    response_model=PageListResponse,
)
def get_pages(
    type_: PageType | None = Query(default=None, alias="type"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Page)
        .options(selectinload(Page.tags))
        .order_by(Page.date.desc(), Page.created_at.desc())
    )

    count_stmt = select(func.count(Page.id))

    if type_ is not None:
        stmt = stmt.where(Page.type == type_)
        count_stmt = count_stmt.where(Page.type == type_)

    total = db.execute(count_stmt).scalar_one()

    items = db.execute(
        stmt.offset((page - 1) * size).limit(size)
    ).scalars().all()

    return PageListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


@router.get(
    "/calendar",
    response_model=list[CalendarPageItem],
)
def get_calendar_pages(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start_date = date(year, month, 1)

    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    items = db.execute(
        select(Page)
        .where(Page.date >= start_date)
        .where(Page.date < end_date)
        .order_by(Page.date.asc(), Page.start_time.asc())
    ).scalars().all()

    return items


@router.get(
    "/search",
    response_model=PageListResponse,
)
def search_pages(
    keyword: str = Query(..., min_length=1),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pattern = f"%{keyword}%"

    base_filter = or_(
        Page.title.ilike(pattern),
        PageBlock.content.ilike(pattern),
    )

    total = db.execute(
        select(func.count(distinct(Page.id)))
        .outerjoin(PageBlock, Page.id == PageBlock.page_id)
        .where(base_filter)
    ).scalar_one()

    items = db.execute(
        select(Page)
        .options(selectinload(Page.tags))
        .outerjoin(PageBlock, Page.id == PageBlock.page_id)
        .where(base_filter)
        .distinct()
        .order_by(Page.date.desc(), Page.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).scalars().all()

    return PageListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


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
    page = get_page_or_404(db, page_id)
    check_page_owner(page, current_user)

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

    if payload.tags is not None:
        page.tags = get_or_create_tags(db, payload.tags)

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
    page = get_page_or_404(db, page_id)
    check_page_owner(page, current_user)

    db.delete(page)
    db.commit()

    return None