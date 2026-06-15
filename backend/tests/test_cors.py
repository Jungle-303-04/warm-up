from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

client = TestClient(app)


def test_allowed_origin_receives_cors_header() -> None:
    origin = get_settings().web_app_url

    response = client.get("/health", headers={"Origin": origin})

    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"
