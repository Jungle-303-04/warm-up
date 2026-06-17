"""LinkFetcher의 httpx 구현(실제 HTTP 호출).

timeout 5초, 리다이렉트 추적, User-Agent 지정. http/https 외 스킴은 호출하지
않는다(SSRF 최소 방어). 오류/타임아웃은 예외를 던지지 않고 html=None 페이지로
돌려준다(application 서비스가 폴백 처리).
"""

import ipaddress
import socket
from urllib.parse import urljoin, urlparse

from app.link_metadata.domain.ports import FetchedPage

_TIMEOUT_SECONDS = 5.0
_USER_AGENT = "RepoLM-LinkPreview/1.0 (+https://github.com)"
# 본문이 지나치게 큰 경우 앞부분만 파싱(메타데이터는 <head>에 있음).
_MAX_BYTES = 512_000
_MAX_REDIRECTS = 5


class HttpxLinkFetcher:
    def fetch(self, url: str) -> FetchedPage:
        # 무거운 의존성은 함수 내 지연 import.
        import httpx

        current_url = url
        try:
            with httpx.Client(
                follow_redirects=False,
                timeout=_TIMEOUT_SECONDS,
                headers={"User-Agent": _USER_AGENT, "Accept": "text/html,*/*"},
            ) as client:
                response = None
                for _ in range(_MAX_REDIRECTS + 1):
                    if not _is_safe_public_http_url(current_url):
                        return FetchedPage(final_url=current_url, content_type=None, html=None)
                    response = client.get(current_url)
                    if response.status_code not in {301, 302, 303, 307, 308}:
                        break
                    location = response.headers.get("location")
                    if not location:
                        break
                    current_url = urljoin(current_url, location)
                if response is None:
                    return FetchedPage(final_url=url, content_type=None, html=None)
        except Exception:
            return FetchedPage(final_url=url, content_type=None, html=None)

        content_type = response.headers.get("content-type")
        final_url = str(response.url)

        if not _is_safe_public_http_url(final_url):
            return FetchedPage(final_url=final_url, content_type=content_type, html=None)

        if "html" not in (content_type or "").lower():
            # 비HTML은 본문 파싱 불필요.
            return FetchedPage(final_url=final_url, content_type=content_type, html=None)

        text = response.text
        if len(text) > _MAX_BYTES:
            text = text[:_MAX_BYTES]
        return FetchedPage(final_url=final_url, content_type=content_type, html=text)


def _is_safe_public_http_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or _default_port(parsed.scheme))
    except socket.gaierror:
        return False
    for info in infos:
        address = info[4][0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            return False
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
            return False
        if ip.is_reserved or ip.is_unspecified:
            return False
    return True


def _default_port(scheme: str) -> int:
    return 443 if scheme == "https" else 80
