"""LinkFetcher의 httpx 구현(실제 HTTP 호출).

timeout 5초, 리다이렉트 추적, User-Agent 지정. http/https 외 스킴은 호출하지
않는다(SSRF 최소 방어). 오류/타임아웃은 예외를 던지지 않고 html=None 페이지로
돌려준다(application 서비스가 폴백 처리).
"""

from app.link_metadata.domain.ports import FetchedPage

_TIMEOUT_SECONDS = 5.0
_USER_AGENT = "RepoLM-LinkPreview/1.0 (+https://github.com)"
# 본문이 지나치게 큰 경우 앞부분만 파싱(메타데이터는 <head>에 있음).
_MAX_BYTES = 512_000


class HttpxLinkFetcher:
    def fetch(self, url: str) -> FetchedPage:
        # 무거운 의존성은 함수 내 지연 import.
        import httpx

        try:
            with httpx.Client(
                follow_redirects=True,
                timeout=_TIMEOUT_SECONDS,
                headers={"User-Agent": _USER_AGENT, "Accept": "text/html,*/*"},
            ) as client:
                response = client.get(url)
        except Exception:
            return FetchedPage(final_url=url, content_type=None, html=None)

        content_type = response.headers.get("content-type")
        final_url = str(response.url)

        if "html" not in (content_type or "").lower():
            # 비HTML은 본문 파싱 불필요.
            return FetchedPage(final_url=final_url, content_type=content_type, html=None)

        text = response.text
        if len(text) > _MAX_BYTES:
            text = text[:_MAX_BYTES]
        return FetchedPage(final_url=final_url, content_type=content_type, html=text)
