from fastapi import APIRouter, status

router = APIRouter()


@router.get(
    "/health",
    response_model=dict[str, str],
    status_code=status.HTTP_200_OK,
)
def health() -> dict[str, str]:
    return {"status": "ok"}
