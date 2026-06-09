from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.pipeline import router as pipeline_router

# api_router는 route 파일들을 한 곳에 모아 main.py가 한 번에 연결할 수 있게 한다.
api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(pipeline_router, prefix="/pipeline")
