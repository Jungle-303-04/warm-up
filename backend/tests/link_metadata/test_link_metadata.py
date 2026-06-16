"""링크 메타데이터 서비스/엔드포인트 테스트(네트워크 금지, fetcher 주입).

가짜 HTML에서 title/description/icon을 파싱하고, 실패/비HTML/잘못된 스킴일 때
s2 favicon으로 폴백하는지 검증한다. 엔드포인트는 get_link_metadata_service를
override해 가짜 fetcher를 쓴다.
"""

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_claims
from app.auth.domain.records import SessionClaims
from app.link_metadata.application.service import LinkMetadataService
from app.link_metadata.dependencies import get_link_metadata_service
from app.link_metadata.domain.ports import FetchedPage
from app.main import app


class _FakeFetcher:
    """주입형 가짜 fetcher. 미리 정한 FetchedPage를 돌려주거나 예외를 던진다."""

    def __init__(self, page: FetchedPage | None = None, raises: bool = False) -> None:
        self._page = page
        self._raises = raises
        self.calls: list[str] = []

    def fetch(self, url: str) -> FetchedPage:
        self.calls.append(url)
        if self._raises:
            raise RuntimeError("network down")
        assert self._page is not None
        return self._page


_HTML = """
<html><head>
<title>폴백 제목</title>
<meta property="og:title" content="OG 제목" />
<meta name="description" content="표준 설명" />
<meta property="og:description" content="OG 설명" />
<link rel="icon" href="/favicon.ico" />
</head><body>본문</body></html>
"""


def test_service_parses_title_description_and_icon() -> None:
    page = FetchedPage(
        final_url="https://example.com/article",
        content_type="text/html; charset=utf-8",
        html=_HTML,
    )
    service = LinkMetadataService(fetcher=_FakeFetcher(page=page))

    result = service.fetch_metadata("https://example.com/article")

    # og:* 가 표준 태그보다 우선.
    assert result.title == "OG 제목"
    assert result.description == "OG 설명"
    # 상대경로 favicon → 절대경로.
    assert result.icon_url == "https://example.com/favicon.ico"


def test_service_falls_back_to_title_tag_when_no_og() -> None:
    html = "<html><head><title>그냥 제목</title></head></html>"
    page = FetchedPage(final_url="https://e.com", content_type="text/html", html=html)
    service = LinkMetadataService(fetcher=_FakeFetcher(page=page))

    result = service.fetch_metadata("https://e.com")

    assert result.title == "그냥 제목"
    assert result.description is None
    # icon 링크 없음 → s2 폴백.
    assert result.icon_url == "https://www.google.com/s2/favicons?domain=e.com&sz=64"


def test_service_fallback_on_fetch_failure() -> None:
    service = LinkMetadataService(fetcher=_FakeFetcher(raises=True))

    result = service.fetch_metadata("https://broken.example.com/x")

    assert result.title is None
    assert result.description is None
    # 실패해도 아이콘은 s2 폴백.
    assert (
        result.icon_url
        == "https://www.google.com/s2/favicons?domain=broken.example.com&sz=64"
    )


def test_service_fallback_on_non_html() -> None:
    page = FetchedPage(
        final_url="https://files.example.com/a.pdf",
        content_type="application/pdf",
        html=None,
    )
    service = LinkMetadataService(fetcher=_FakeFetcher(page=page))

    result = service.fetch_metadata("https://files.example.com/a.pdf")

    assert result.title is None
    assert result.description is None
    assert (
        result.icon_url
        == "https://www.google.com/s2/favicons?domain=files.example.com&sz=64"
    )


def test_service_rejects_non_http_scheme() -> None:
    fetcher = _FakeFetcher(raises=True)
    service = LinkMetadataService(fetcher=fetcher)

    result = service.fetch_metadata("ftp://internal/secret")

    # SSRF 최소 방어: http/https가 아니면 fetch 자체를 호출하지 않는다.
    assert fetcher.calls == []
    assert result.title is None
    assert result.description is None
    assert result.icon_url is None


@pytest.fixture
def _client_with_fake_fetcher():
    page = FetchedPage(
        final_url="https://example.com",
        content_type="text/html",
        html=_HTML,
    )
    app.dependency_overrides[get_current_claims] = lambda: SessionClaims(
        user_id=1, login="t"
    )
    app.dependency_overrides[get_link_metadata_service] = (
        lambda: LinkMetadataService(fetcher=_FakeFetcher(page=page))
    )
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_endpoint_returns_parsed_metadata(_client_with_fake_fetcher) -> None:
    response = _client_with_fake_fetcher.get(
        "/link-metadata", params={"url": "https://example.com"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "OG 제목"
    assert body["description"] == "OG 설명"
    assert body["icon_url"] == "https://example.com/favicon.ico"


def test_endpoint_requires_url_param(_client_with_fake_fetcher) -> None:
    response = _client_with_fake_fetcher.get("/link-metadata")
    # url 쿼리 파라미터 필수.
    assert response.status_code == 422
