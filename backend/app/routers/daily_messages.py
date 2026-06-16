from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.daily_message import DailyMessage
from app.models.user import User
from app.schemas.daily_message_schema import (
    DailyMessageCreate,
    DailyMessageResponse,
    DailyMessageUpdate,
)

# 오늘의 한마디 API는 모두 /daily-messages 아래로 묶는다.
router = APIRouter(prefix="/daily-messages", tags=["Daily Messages"])


def get_daily_message_or_404(db: Session, message_id: int) -> DailyMessage:
    # 수정/삭제/상세 처리 전에 해당 id의 한마디가 실제로 있는지 찾는다.
    # author도 같이 불러와야 응답에서 작성자 닉네임을 바로 내려줄 수 있다.
    message = db.execute(
        select(DailyMessage)
        .options(selectinload(DailyMessage.author))
        .where(DailyMessage.id == message_id)
    ).scalar_one_or_none()

    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="오늘의 한마디를 찾을 수 없습니다.",
        )

    return message


def check_daily_message_owner(message: DailyMessage, current_user: User) -> None:
    # 수정과 삭제는 작성자 본인만 할 수 있다.
    # 프론트에서 버튼을 숨기더라도 백엔드에서 한 번 더 권한을 검증한다.
    if message.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="작성자만 수정하거나 삭제할 수 있습니다.",
        )


@router.get("", response_model=list[DailyMessageResponse])
def get_daily_messages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 로그인한 사용자는 팀 전체가 작성한 오늘의 한마디 목록을 볼 수 있다.
    # 최신 글이 위에 오도록 created_at 내림차순으로 정렬한다.
    return (
        db.execute(
            select(DailyMessage)
            .options(selectinload(DailyMessage.author))
            .order_by(DailyMessage.created_at.desc())
        )
        .scalars()
        .all()
    )


@router.post(
    "",
    response_model=DailyMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_daily_message(
    payload: DailyMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 작성자는 프론트가 보내지 않는다.
    # JWT 토큰으로 확인한 current_user.id를 author_id로 저장한다.
    message = DailyMessage(
        author_id=current_user.id,
        content=payload.content.strip(),
    )

    if not message.content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="내용을 입력해 주세요.",
        )

    db.add(message)
    db.commit()

    # commit 후 author 관계까지 포함된 최신 객체를 다시 조회해서 응답한다.
    return get_daily_message_or_404(db, message.id)


@router.patch("/{message_id}", response_model=DailyMessageResponse)
def update_daily_message(
    message_id: int,
    payload: DailyMessageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. 수정하려는 한마디를 찾는다.
    # 2. 현재 사용자가 작성자인지 확인한다.
    # 3. 통과하면 content를 수정한다.
    message = get_daily_message_or_404(db, message_id)
    check_daily_message_owner(message, current_user)

    content = payload.content.strip()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="내용을 입력해 주세요.",
        )

    message.content = content
    db.commit()

    return get_daily_message_or_404(db, message.id)


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_daily_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 삭제도 수정과 마찬가지로 작성자 본인인지 먼저 확인한다.
    message = get_daily_message_or_404(db, message_id)
    check_daily_message_owner(message, current_user)

    db.delete(message)
    db.commit()

    return None
