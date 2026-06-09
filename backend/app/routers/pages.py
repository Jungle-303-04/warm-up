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

# 태그 이름 목록 받아서 
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
    response_model=PageResponse, #클라에게 반환
    status_code=status.HTTP_201_CREATED,
)
def create_page(
    payload: PageCreate, #클라가 보낸 JSON body
    db: Session = Depends(get_db), #작업용 세션
    current_user: User = Depends(get_current_user), #현재 로그인한 유저
):
    #새 page 객체 생성
    page = Page(
        type=payload.type,
        title=payload.title,
        date=payload.date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        author_id=current_user.id,
        participants=payload.participants,
    )

    #페이지에 태그 붙인다
    page.tags = get_or_create_tags(db, payload.tags)

    db.add(page) # db에 저장 준비
    db.flush() #db에 INSERT보내서 page.id 먼저 받아와라

    for index, block in enumerate(payload.blocks): #블록 만든다
        page_block = PageBlock(
            page_id=page.id,
            type=block.type,
            content=block.content,
            checked=block.checked,
            order_index=index,
        )
        db.add(page_block)

    db.commit() #db 저장

    return get_page_or_404(db, page.id) #방금 만든 페이지 다시 db에서 조회해서 반환한다

# 페이지 목록 가져오는 API
@router.get(
    "",
    response_model=PageListResponse,
)
def get_pages(
    type_: PageType | None = Query(default=None, alias="type"), #회의 or 회고
    page: int = Query(default=1, ge=1), # 몇번째 페이지인지
    size: int = Query(default=10, ge=1, le=100), #한 페이지에 몇개 가져올지
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    #SELECT *
    #FROM pages
    #ORDER BY date DESC, created_at DESC;
    #쿼리문이다
    stmt = (
        select(Page)
        .options(selectinload(Page.tags))
        .order_by(Page.date.desc(), Page.created_at.desc())
    )

    #전체 페이지 개수
    #쿼리문이다
    count_stmt = select(func.count(Page.id))

    #type이 있으면
    if type_ is not None:
        #쿼리문이다
        stmt = stmt.where(Page.type == type_) #db에서 page의 type이 type_인거 조회해라
        #쿼리문이다
        count_stmt = count_stmt.where(Page.type == type_) #db에서 page의 type이 type_인 개수

    total = db.execute(count_stmt).scalar_one() #회의만 조회하면 회의 총 개수만 나온다

    #db에서 현재 페이지에 보여줄 데이터만 가져온다
    items = db.execute(
        stmt.offset((page - 1) * size).limit(size)
    ).scalars().all() #DB 결과에서 Page 객체들만 리스트로 꺼낸다

    return PageListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )

#특정 월에 해당하는 회의/회고를 가져온다
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

    #db에서 특정 월 데이터만 가져온다
    items = db.execute(
        select(Page)
        .where(Page.author_id == current_user.id)
        .where(Page.date >= start_date)
        .where(Page.date < end_date)
        .order_by(Page.date.asc(), Page.start_time.asc()) #날짜 빠른순서, 같은 날짜면 시작시간 빠른 순서
    ).scalars().all()

    return items


# 제목이나 본문에 검색어가 포함된 회의/회고를 찾는다
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

    # 검색어가 제목에 있든 본문에 있든 하나라도 맞으면 가져와라
    base_filter = or_(
        Page.title.ilike(pattern), #페이지 제목에 keyword가 있거나
        PageBlock.content.ilike(pattern), #본문 블록 내용에 keyword가 있으면 검색 결과에 포함
    )

    #검색어에 걸린 페이지가 총 몇 개인지 세는 코드
    total = db.execute(
        select(func.count(distinct(Page.id))) #중복 제거한 page 개수만 세라
        .outerjoin(PageBlock, Page.id == PageBlock.page_id) #page랑 pageBlock을 연결해서 조회하겠다
        .where(base_filter)
    ).scalar_one()


    items = db.execute(
        select(Page)
        .options(selectinload(Page.tags))
        .outerjoin(PageBlock, Page.id == PageBlock.page_id) #pages랑 page_block 연결
        .where(base_filter) #제목에 검색어가 있거나 본문 블록 내용에 검색어가 있으면
        .distinct() #중복 페이지 제거
        .order_by(Page.date.desc(), Page.created_at.desc()) #정렬
        .offset((page - 1) * size) #페이지 네이션
        .limit(size)
    ).scalars().all() #page 객체들만 리스트로 꺼낸다

    return PageListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )

# 특정 회의/회고 하나의 상세 정보를 가져온다
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
    #page_id에 해당하는 페이지 DB에서 찾는다
    page = get_page_or_404(db, page_id)
    check_page_owner(page, current_user) #이 페이지가 현재 로그인한 사용자의 페이지인지 확인

    #payload에 값이 있으면 page에 덮어쓰기
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
