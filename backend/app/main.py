from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

#FastAPI 서버 객체 만들고, 여기다가 api 등록
app = FastAPI(
    title = "TeamLog API",
    description = "Calendar-based meeting and retrospective collaboration tool",
    version = "0.1.0",
)

#프론트와 백의 주소가 다르기 때문에 백에서 프론트의 요청을 막을 수 있다 -> 하지만 밑에 코드로 프론트의 주소를 등록해서 해당 주소의 요청을 허용한다
#React 프론트엔드가 FASTAPI 백엔드에 요청할 수 있게 CORS 허용 설정을 추가하는 코드
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#FASTAPI 서버 살아있는지 확인 -> 클라이언트한테 return 값 보내준다
@app.get("/health")
def health_check():
    return {
        "status" : "ok",
        "message": "TeamLog API is running",
    }

#FastAPI가 DB와 연결되는지 확인-> 
@app.get("/db-health")
def db_health_check(db : Session = Depends(get_db)):
    result = db.execute(text("SELECT 1")).scalar()
    return {
        "status": "ok",
        "db": result,
    }

#PostgreSQL에 vector extension이 켜져 있는지 확인
@app.get("/pgvector-health")
def pgvector_health_check(db: Session = Depends(get_db)):
    result = db.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'"),
            ).scalar() #pgvector 설치되어 있으면 vector 반환
    return {
        "status" : "ok" if result == "vector" else "error",
        "extension" : result,
    }