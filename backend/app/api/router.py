from fastapi import APIRouter, status
from fastapi.responses import RedirectResponse

from app.health.router import router as health_router
from app.pipeline.router import router as pipeline_router
from app.repo_rag.router import router as repo_rag_router

api_router = APIRouter()


@api_router.get("/", include_in_schema=False, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
def redirect_to_docs() -> RedirectResponse:
    return RedirectResponse(url="/api/docs")


api_router.include_router(health_router, tags=["health"])
api_router.include_router(pipeline_router, prefix="/pipeline", tags=["pipeline"])
api_router.include_router(repo_rag_router, prefix="/pipeline", tags=["repo-rag"])
