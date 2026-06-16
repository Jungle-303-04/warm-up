"""링크 메타데이터 의존성 배선.

httpx 어댑터를 LinkMetadataService에 주입한다. 테스트는 이 의존성을
override해 가짜 fetcher를 주입한다(네트워크 금지).
"""

from app.link_metadata.application.service import LinkMetadataService
from app.link_metadata.infrastructure.httpx_fetcher import HttpxLinkFetcher


def get_link_metadata_service() -> LinkMetadataService:
    return LinkMetadataService(fetcher=HttpxLinkFetcher())
