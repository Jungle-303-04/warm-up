from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from database import engine
from models.post import Post

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

@app.get("/posts")
def get_posts():
    # 앨범형으로 할 예정 (제목, 폰트가 적용된 모습, 폰트 태그 정도?)
    # 등록된 게시글 모두 가져오기
    # db 연결 확인 후 id로 불러오기
    # response는 게시글 표시에 필요한 (제목, 폰트 태그 이 것만 응답데이터로 넣으면 될 듯)
    with Session(engine) as session:
        # posts 테이블의 모든 row가져오기
        posts = session.exec(select(Post)).all()
        return posts

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/posts")
def create_post():
    # 프론트에서 받은 제목, 내용, font 데이터, user정보(user 정보는 아직 table 생성안했음)
    # 내용 2차 검토(프론트에서 1차 서버에서 받을 수 없는 형태라던지, 검토 후 등록)
    # db에 저장 후 성공여부랑 데이터 반환해야함. 프론트가 등록직후에 상세페이지로 이동 또는 게시글 목륵에 추가하려면필요
    # 여기 동시성 제어 해야하는지 궁금
    return {"result" : ""}

@app.get("/posts/{post_id}")
def get_post(post_id : int):
    # post_id가 db와 일치하는 id가 있는지 확인하고, (아마 게시물 마다 id로 들어올듯)
    # 해당하는 게시물 가져오기
    # 응답은 해당 게시물에 대한 화면에 표시할 데이터 반환 (제목, 폰트 태그 이 것만 응답데이터로 넣으면 될 듯) 
    return {"result" : ""}

@app.put("/posts/{post_id}")
def update_post(post_id : int):
    # 해당 id를 받아서 수정할 내용을 매칭시킴 (제목, 내용, 폰트 정보)
    # 해당 id를 db에서 찾아서 내용를 수정하고 다시 db에 저장하기
    # 성공 여부만 반환하기
    return {"result" : ""}

@app.delete("/posts/{post_id}")
def delete_post(post_id : int):
    # 해당 post_id를 db에서 찾아서 있으면 삭제하고 결과반환
    return {"result" : ""}
