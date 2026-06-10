from fastapi import FastAPI

from app.api.router import api_router

app = FastAPI(
    title="RepoPilot API",
    version="0.1.0",
    summary="Minimal API surface for the RepoPilot pipeline",
)

app.include_router(api_router)
