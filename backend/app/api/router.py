from fastapi import APIRouter, status
from fastapi.responses import RedirectResponse

from app.github.api.router import router as github_router
from app.health.api.router import router as health_router
from app.pipeline.api.router import router as pipeline_router
from app.proposals.api.router import router as proposals_router
from app.repo_rag.api.router import router as repo_rag_router

api_router = APIRouter()


@api_router.get("/", include_in_schema=False, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
def redirect_to_docs() -> RedirectResponse:
    return RedirectResponse(url="/api/docs")


api_router.include_router(health_router, tags=["health"])
api_router.include_router(pipeline_router, prefix="/pipeline", tags=["pipeline"])
api_router.include_router(repo_rag_router, prefix="/pipeline", tags=["repo-rag"])
api_router.include_router(proposals_router, prefix="/pipeline", tags=["proposals"])
api_router.include_router(github_router, prefix="/github", tags=["github"])
