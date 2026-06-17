from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Request
from sqlmodel import SQLModel, Session, select

from database import engine
from models.comment import Comment
from models.post import Post
from models.user import User
from routers.auth import get_current_user_from_access_token

router = APIRouter()


class CommentCreate(SQLModel):
    content: str


class CommentRead(SQLModel):
    id: int
    content: str
    post_id: int
    user_id: int
    nickname: str
    created_at: datetime


def build_comment_response(session: Session, comment: Comment) -> CommentRead:
    user = session.get(User, comment.user_id)

    if user is None:
        raise HTTPException(
            status_code=500,
            detail="댓글 작성자 정보를 찾을 수 없습니다.",
        )

    return CommentRead(
        id=comment.id,
        content=comment.content,
        post_id=comment.post_id,
        user_id=comment.user_id,
        nickname=user.nickname,
        created_at=comment.created_at,
    )


@router.get("/posts/{post_id}/comments", response_model=List[CommentRead])
def get_comments(post_id: int):
    with Session(engine) as session:
        post = session.get(Post, post_id)

        if post is None:
            raise HTTPException(
                status_code=404,
                detail="게시글을 찾을 수 없습니다.",
            )

        comments = session.exec(
            select(Comment)
            .where(Comment.post_id == post_id)
            .order_by(Comment.created_at.asc())
        ).all()

        comment_responses = []

        for comment in comments:
            comment_response = build_comment_response(session, comment)
            comment_responses.append(comment_response)

        return comment_responses


@router.post("/posts/{post_id}/comments", response_model=CommentRead)
def create_comment(post_id: int, comment_data: CommentCreate, request: Request):
    if not comment_data.content.strip():
        raise HTTPException(
            status_code=400,
            detail="댓글 내용은 필수 입력 항목입니다.",
        )

    current_user = get_current_user_from_access_token(request)

    with Session(engine) as session:
        post = session.get(Post, post_id)

        if post is None:
            raise HTTPException(
                status_code=404,
                detail="게시글을 찾을 수 없습니다.",
            )

        comment = Comment(
            content=comment_data.content,
            post_id=post_id,
            user_id=current_user.id,
        )

        session.add(comment)
        session.commit()
        session.refresh(comment)

        return build_comment_response(session, comment)


@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: int):
    with Session(engine) as session:
        comment = session.get(Comment, comment_id)

        if comment is None:
            raise HTTPException(
                status_code=404,
                detail="댓글을 찾을 수 없습니다.",
            )

        session.delete(comment)
        session.commit()

        return {
            "success": True,
            "message": "댓글 삭제 완료",
        }
