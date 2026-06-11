from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from app.api.routes.health import router as health_router
from app.api.routes.pipeline import router as pipeline_router

api_router = APIRouter()


@api_router.get("/", include_in_schema=False)
def redirect_to_docs() -> RedirectResponse:
    return RedirectResponse(url="/docs")


api_router.include_router(health_router)
api_router.include_router(pipeline_router, prefix="/pipeline")
