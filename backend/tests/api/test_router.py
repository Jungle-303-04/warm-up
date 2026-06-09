from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.router import api_router

app = FastAPI()
app.include_router(api_router)
client = TestClient(app)


def test_api_router_collects_health_and_pipeline_routes() -> None:
    assert client.get("/health").status_code == 200
    assert client.get("/pipeline").status_code == 200
