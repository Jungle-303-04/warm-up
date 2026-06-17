from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from database import engine
from models.post import Post, PostCreate
from models.font import Font
from models.user import User
from models.recommend import (RecommendRequest, RecommendResponse)

from datetime import datetime, timezone
from agent.recommend_agent import run_recommend_agent
from routers.comments import router as comments_router
from routers.auth import router as auth_router
from routers.auth import get_current_user_from_access_token

app = FastAPI()

app.include_router(comments_router)
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message" : "connected backend"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/posts")
def get_posts():

    with Session(engine) as session:
        # posts 테이블의 모든 row가져오기
        posts = session.exec(select(Post)).all()
        result = []
        for post in posts:

            font = session.get(Font, post.font_id)
            user = session.get(User, post.user_id)

            result.append(
                {
                    "id": post.id,
                    "title": post.title,
                    "content": post.content,
                    "recommend_reason": post.recommend_reason,
                    "created_at": post.created_at,
                    "user": {
                        "nickname": user.nickname
                    },
                    "font": {
                        "id": font.id,
                        "name": font.name,
                        "tags": font.tags
                    } 
                }
            )
        
        return result

@app.post("/posts")
def create_post(post_data: PostCreate, request: Request):

    current_user = get_current_user_from_access_token(request)
    title = post_data.title.strip()
    content = post_data.content.strip()
    recommend_reason = post_data.recommend_reason.strip()

    if not title:
        raise HTTPException(status_code=400, detail="제목은 필수 입력 항목입니다.")

    if not content:
        raise HTTPException(status_code=400, detail="내용은 필수 입력 항목입니다.")

    if not recommend_reason:
        raise HTTPException(status_code=400, detail="추천 이유는 필수 입력 항목입니다.")

    # postgreSQL 연결 시작 수행 후 종료
    with Session(engine) as session:
        font = session.get(Font, post_data.font_id)

        if font is None:
            raise HTTPException(status_code=400, detail="폰트 정보를 찾을 수 없습니다.")

        post = Post(
            title=title,
            content=content,
            recommend_reason=recommend_reason,
            font_id=post_data.font_id,
            user_id=current_user.id
        )

        # 객체 등록 (저장 대기열)
        session.add(post)
        # 객체 DB 반영
        session.commit()
        # DB 반영 조회 (최신 상태로 객체 갱신)
        session.refresh(post)
        # fast API 자동 json으로 변환해줌
        return {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "recommend_reason": post.recommend_reason,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "user": {
                "id": current_user.id,
                "nickname": current_user.nickname
            },
            "font": {
                "id": font.id,
                "name": font.name,
                "tags": font.tags
            }
        }

@app.get("/posts/{post_id}")
def get_post(post_id : int): 

    with Session(engine) as session:
        # 해당 id의 Row 가져오기
        post = session.get(Post, post_id)
        if post is None:
            raise HTTPException(
                status_code=404,
                detail="게시글을 찾을 수 없습니다."
            )
        
        font = session.get(Font, post.font_id)
        if font is None:
            raise HTTPException(
                status_code=500,
                detail="게시글과 연결된 폰트 정보를 찾을 수 없습니다."
    )
        
        user = session.get(User, post.user_id)

        return  {
                    "id": post.id,
                    "title": post.title,
                    "content": post.content,
                    "recommend_reason": post.recommend_reason,
                    "created_at": post.created_at,
                    "updated_at": post.updated_at,
                    "user": {
                        "id": user.id,
                        "nickname": user.nickname
                    },
                    "font": {
                        "id": font.id,
                        "name": font.name,
                        "tags": font.tags
                    } 
                }

@app.put("/posts/{post_id}")
def update_post(post_id: int, post_data: PostCreate, request: Request):

    current_user = get_current_user_from_access_token(request)
    title = post_data.title.strip()
    content = post_data.content.strip()
    recommend_reason = post_data.recommend_reason.strip()

    if not title:
        raise HTTPException(status_code=400, detail="제목은 필수 입력 항목입니다.")

    if not content:
        raise HTTPException(status_code=400, detail="내용은 필수 입력 항목입니다.")

    if not recommend_reason:
        raise HTTPException(status_code=400, detail="추천 이유는 필수 입력 항목입니다.")
    
    with Session (engine) as session:
        post = session.get(Post, post_id)

        if post is None:
            # FastAPI 제공 예외 클래스로 정확한 상태코드 내려줌
            raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

        if post.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="게시글 수정 권한이 없습니다.")

        font = session.get(Font, post_data.font_id)

        if font is None:
            raise HTTPException(status_code=400, detail="폰트 정보를 찾을 수 없습니다.")

        post.title = title
        post.content = content
        post.recommend_reason = recommend_reason
        post.font_id = post_data.font_id
        post.updated_at = datetime.now(timezone.utc)

        session.add(post)
        session.commit()
        session.refresh(post)

        return {
            "success": True,
            "message": "게시글 수정 완료"
        }


@app.delete("/posts/{post_id}")
def delete_post(post_id : int, request: Request):
    # 해당 post_id를 db에서 찾아서 있으면 삭제하고 결과반환

    current_user = get_current_user_from_access_token(request)

    with Session (engine) as session:
        post = session.get(Post, post_id)

        if post is None:
            raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
        
        if post.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="게시글 삭제 권한이 없습니다.")

        session.delete(post)
        session.commit()

        return {
            "success": True,
            "message": "게시글 삭제 완료"
        }

@app.post("/recommend", response_model=RecommendResponse)
def recommend_fonts(request: RecommendRequest):
    try:
        return run_recommend_agent(request)

    # agent 내부 예외 전달
    except HTTPException:
        raise

    # 파이썬 기본 예외들의 부모 클래스
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="추천 처리 중 오류가 발생했습니다.",
        )
