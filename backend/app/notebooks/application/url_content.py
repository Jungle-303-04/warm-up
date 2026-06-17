"""URL 소스 본문 추출 헬퍼.

링크 미리보기와 달리 RAG 인덱싱에는 제목/설명뿐 아니라 실제 페이지 본문
후보가 필요하다. HTTP 호출은 SSRF 방어가 들어간 LinkFetcher 포트를 통해서만
수행하고, 이 모듈은 HTML을 안전하게 정제한 텍스트로 바꾸는 책임만 가진다.
"""

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from app.link_metadata.application.service import LinkMetadataService

if TYPE_CHECKING:
    from app.link_metadata.domain.ports import LinkFetcher


MAX_URL_TEXT_CHARS = 80_000
_SKIPPED_TAGS = {"script", "style", "noscript", "svg", "canvas"}
_BLOCK_TAGS = {
    "title",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "p",
    "li",
    "blockquote",
    "pre",
    "code",
    "td",
    "th",
}


@dataclass(frozen=True, slots=True)
class UrlDocument:
    title: str
    url: str
    text: str


class UrlContentExtractor:
    def __init__(self, fetcher: "LinkFetcher") -> None:
        self._fetcher = fetcher

    def fetch_document(self, url: str, *, fallback_title: str | None = None) -> UrlDocument | None:
        normalized = normalize_http_url(url)
        page = self._fetcher.fetch(normalized)
        metadata = LinkMetadataService(self._fetcher).metadata_from_page(normalized, page)
        text_parts = [
            metadata.title,
            metadata.description,
            _extract_readable_text(page.html or ""),
        ]
        text = _normalize_text("\n\n".join(part for part in text_parts if part))
        if not text:
            return None
        return UrlDocument(
            title=metadata.title or fallback_title or _host_title(normalized),
            url=page.final_url or normalized,
            text=text[:MAX_URL_TEXT_CHARS],
        )


def normalize_http_url(url: str) -> str:
    normalized = (url or "").strip()
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("url 소스는 http 또는 https URL만 지원합니다")
    return normalized


class _ReadableTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._capture_stack: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in _SKIPPED_TAGS:
            self._skip_depth += 1
            return
        if tag in _BLOCK_TAGS:
            self._capture_stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _SKIPPED_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
            return
        if tag in _BLOCK_TAGS and self._capture_stack:
            self._capture_stack.pop()
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0 or not self._capture_stack:
            return
        text = data.strip()
        if text:
            self.parts.append(text)


def _extract_readable_text(html: str) -> str:
    if not html:
        return ""
    parser = _ReadableTextParser()
    try:
        parser.feed(html)
    except Exception:
        return ""
    return _normalize_text(" ".join(parser.parts))


def _normalize_text(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.splitlines()]
    compact: list[str] = []
    previous = ""
    for line in lines:
        if not line or line == previous:
            continue
        compact.append(line)
        previous = line
    return "\n".join(compact).strip()


def _host_title(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc or url
