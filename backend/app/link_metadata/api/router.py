from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_current_claims
from app.link_metadata.api.schemas import LinkMetadataResponse
from app.link_metadata.application.service import LinkMetadataService
from app.link_metadata.dependencies import get_link_metadata_service

router = APIRouter()


@router.get(
    "/link-metadata",
    response_model=LinkMetadataResponse,
    dependencies=[Depends(get_current_claims)],
)
def get_link_metadata(
    url: str = Query(..., description="제목/설명/아이콘을 조회할 대상 URL"),
    service: LinkMetadataService = Depends(get_link_metadata_service),
) -> LinkMetadataResponse:
    # 실패/타임아웃/비HTML이어도 에러 대신 가능한 필드만 채워서 반환함
    metadata = service.fetch_metadata(url)
    return LinkMetadataResponse.from_metadata(metadata)
