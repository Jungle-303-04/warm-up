from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from database import engine
from models.post import Post
from models.font import Font
from models.user import User

from datetime import datetime, timezone

app = FastAPI()

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

            result.append(
                {
                    "id": post.id,
                    "title": post.title,
                    "content": post.content,
                    "created_at": post.created_at,
                    "font": {
                        "name": font.name,
                        "tags": font.tags
                    } 
                }
            )
        
        return result

@app.post("/posts")
def create_post(post_data : Post):

    # postgreSQL 연결 시작 수행 후 종료
    with Session(engine) as session:
        # 객체 등록 (저장 대기열)
        session.add(post_data)
        # 객체 DB 반영
        session.commit()
        # DB 반영 조회 (최신 상태로 객체 갱신)
        session.refresh(post_data)
        # fast API 자동 json으로 변환해줌
        return post_data

@app.get("/posts/{post_id}")
def get_post(post_id : int): 

    with Session(engine) as session:
        # 해당 id의 Row 가져오기
        post = session.get(Post, post_id)

        if post is None:
            return {"message": "게시글 없음"}

        return post

@app.put("/posts/{post_id}")
def update_post(post_id : int, post_data: Post):
    with Session (engine) as session:
        post = session.get(Post, post_id)

        if post is None:
            # FastAPI 제공 예외 클래스로 정확한 상태코드 내려줌
            raise HTTPException(status_code=404, detail="Post not found")

        post.title = post_data.title
        post.content = post_data.content
        post.user_id = post_data.user_id
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
def delete_post(post_id : int):
    # 해당 post_id를 db에서 찾아서 있으면 삭제하고 결과반환

    with Session (engine) as session:
        post = session.get(Post, post_id)

        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")

        session.delete(post)
        session.commit()

        return {
            "success": True,
            "message": "게시글 삭제 완료"
        }
