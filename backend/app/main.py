from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.routers import ai, auth, daily_messages, pages

# FastAPI 앱을 만든다 -> 백엔드 서버의 중심 객체
# FastAPI 앱 인스턴스를 만든다. 이 객체가 백엔드 서버의 중심 역할을 한다.
app = FastAPI(
    title="TeamLog API",
    description="Calendar-based meeting and retrospective collaboration tool",
    version="0.1.0",
)


# CORS 설정(프론트엔드와 백엔드 주소가 다를 때, 브라우저가 요청을 막는 보안 규칙)
# CORS 설정이다. 프론트엔드 주소에서 오는 요청을 백엔드가 허용하게 만든다.
app.add_middleware(
    CORSMiddleware,  # 요청이 들어올 때마다 출처를 확인하고 허용할지 말지 처리
    allow_origins=[settings.FRONTEND_URL],  # 주소에서 온 요청만 허용
    allow_credentials=True,  # 쿠키나 인증 정보를 포함한 요청도 허용
    allow_methods=["*"],  # 모든 HTTP 메서드 허용(GET POST 등등)
    allow_headers=["*"],  # 모든 요청 헤더 허용
)

# 다른 파일에 있는 API들을 이 앱에 붙인다
# auth, pages 라우터에 정의된 API들을 현재 FastAPI 앱에 연결한다.
app.include_router(auth.router)  # signup, login, me
app.include_router(pages.router)  #
app.include_router(daily_messages.router)  # /daily-messages
app.include_router(ai.router)  # /ai/rag/query


# 서버가 살아 있는지 간단히 확인하는 API다. DB는 확인하지 않는다.
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "TeamLog API is running",
    }


# DB 세션을 받아 SELECT 1을 실행해서 데이터베이스 연결 상태를 확인한다.
@app.get("/db-health")
def db_health_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1")).scalar()
    return {
        "status": "ok",
        "db": result,
    }


# PostgreSQL에 pgvector 확장이 설치되어 있는지 확인한다.
@app.get("/pgvector-health")
def pgvector_health_check(db: Session = Depends(get_db)):
    result = db.execute(
        text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
    ).scalar()

    return {
        "status": "ok" if result == "vector" else "error",
        "extension": result,
    }
