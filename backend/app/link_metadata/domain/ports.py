"""링크 메타데이터 포트.

도메인이 소유하는 추상. application 서비스는 LinkFetcher 포트에만 의존하고,
실제 HTTP 호출은 infrastructure httpx 어댑터가 구현한다(DIP). 테스트는 가짜
fetcher를 주입해 네트워크 없이 검증한다.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class FetchedPage:
    """가져온 페이지의 최소 정보.

    final_url: 리다이렉트 후 최종 URL(상대경로 favicon 절대화에 사용).
    content_type: 응답 Content-Type(HTML 여부 판별). 실패/비HTML이면 html=None.
    html: HTML 본문(파싱 가능할 때만). 그 외 None.
    """

    final_url: str
    content_type: str | None
    html: str | None


class LinkFetcher(Protocol):
    def fetch(self, url: str) -> FetchedPage:
        """URL을 GET 한다. 실패/타임아웃이면 html=None인 FetchedPage를 돌려준다."""
        ...
