from fastapi import FastAPI

from app.api.router import api_router

# main.py는 FastAPI 앱 생성과 전체 router 연결만 담당한다.
app = FastAPI(
    title="RepoPilot API",
    version="0.1.0",
    summary="Minimal API surface for the RepoPilot pipeline",
)

app.include_router(api_router)
