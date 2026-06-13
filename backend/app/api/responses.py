from typing import Any

from fastapi import status
from pydantic import BaseModel

from app.api.schemas import ErrorResponse


OpenApiResponse = dict[int, dict[str, Any]]


def error_response(status_code: int, model: type[BaseModel] = ErrorResponse) -> OpenApiResponse:
    return {status_code: {"model": model}}


BAD_REQUEST_RESPONSE = error_response(status.HTTP_400_BAD_REQUEST)
