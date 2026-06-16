"""링크 메타데이터 유스케이스.

주어진 URL의 HTML에서 제목/설명/아이콘(favicon)을 뽑아낸다. 파싱은 표준
라이브러리 html.parser만 사용하고(새 의존성 금지), 실제 HTTP는 LinkFetcher
포트로 주입받는다(헥사고날 경계). 실패/타임아웃/비HTML이면 에러 대신 가능한
필드만 채우고 나머지는 null로 두며, icon_url은 항상 google s2 favicon으로 폴백한다.

SSRF 최소 방어: http/https 스킴만 허용한다.
"""

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlparse

if TYPE_CHECKING:
    from app.link_metadata.domain.ports import LinkFetcher


@dataclass(slots=True)
class LinkMetadata:
    title: str | None
    description: str | None
    icon_url: str | None


class _MetaParser(HTMLParser):
    """<title>/메타 태그/아이콘 링크를 한 번의 패스로 수집한다.

    og:title/og:description은 표준 title/description보다 우선한다.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: str | None = None
        self.og_title: str | None = None
        self.description: str | None = None
        self.og_description: str | None = None
        self.icon_href: str | None = None
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self._in_title = True
            return

        attr = {key.lower(): (value or "") for key, value in attrs}

        if tag == "meta":
            prop = (attr.get("property") or attr.get("name") or "").lower()
            content = attr.get("content")
            if not content:
                return
            if prop == "og:title" and self.og_title is None:
                self.og_title = content.strip()
            elif prop == "og:description" and self.og_description is None:
                self.og_description = content.strip()
            elif prop == "description" and self.description is None:
                self.description = content.strip()
        elif tag == "link":
            rel = (attr.get("rel") or "").lower()
            href = attr.get("href")
            # rel="icon" / "shortcut icon" / "apple-touch-icon" 등 첫 아이콘만 사용.
            if href and self.icon_href is None and "icon" in rel:
                self.icon_href = href.strip()

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title and self.title is None:
            text = data.strip()
            if text:
                self.title = text


@dataclass(slots=True)
class LinkMetadataService:
    fetcher: "LinkFetcher"

    def fetch_metadata(self, url: str) -> LinkMetadata:
        normalized = (url or "").strip()
        host = self._host(normalized)

        # SSRF 최소 방어: http/https만 허용. 그 외 스킴은 아무것도 조회하지 않음.
        if not self._is_http_url(normalized):
            return LinkMetadata(title=None, description=None, icon_url=None)

        try:
            page = self.fetcher.fetch(normalized)
        except Exception:
            # 어떤 오류든 폴백(아이콘만 s2로 제공).
            return LinkMetadata(
                title=None, description=None, icon_url=self._favicon_fallback(host)
            )

        if not page.html or not self._is_html(page.content_type):
            # 비HTML/빈 응답: 제목·설명 없이 아이콘만 폴백.
            return LinkMetadata(
                title=None, description=None, icon_url=self._favicon_fallback(host)
            )

        parser = _MetaParser()
        try:
            parser.feed(page.html)
        except Exception:
            parser = _MetaParser()  # 파싱 실패 시 빈 결과로 폴백

        title = parser.og_title or parser.title
        description = parser.og_description or parser.description
        icon_url = self._resolve_icon(parser.icon_href, page.final_url or normalized, host)

        return LinkMetadata(
            title=title or None,
            description=description or None,
            icon_url=icon_url,
        )

    @staticmethod
    def _is_http_url(url: str) -> bool:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)

    @staticmethod
    def _is_html(content_type: str | None) -> bool:
        if not content_type:
            # Content-Type이 없으면 일단 HTML로 시도(파서가 안전하게 처리).
            return True
        return "html" in content_type.lower()

    @staticmethod
    def _host(url: str) -> str:
        return urlparse(url).netloc

    def _resolve_icon(self, href: str | None, base_url: str, host: str) -> str | None:
        if href:
            # <link rel="icon">가 있으면 절대경로로 변환.
            absolute = urljoin(base_url, href)
            if self._is_http_url(absolute):
                return absolute
        return self._favicon_fallback(host)

    @staticmethod
    def _favicon_fallback(host: str) -> str | None:
        if not host:
            return None
        return f"https://www.google.com/s2/favicons?domain={host}&sz=64"
