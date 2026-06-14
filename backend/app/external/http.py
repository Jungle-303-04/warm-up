from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any, Protocol

import httpx


HttpRequestCallback = Callable[["HttpRequest"], "HttpRequest"]
HttpResponseCallback = Callable[["HttpRequest", httpx.Response], httpx.Response]


@dataclass(frozen=True)
class HttpRequest:
    """외부 HTTP 호출에 필요한 값을 하나의 객체로 묶어 필터가 안전하게 수정하게 한다."""

    method: str
    url: str
    headers: dict[str, str]
    timeout: int
    data: dict[str, Any] | None = None
    json: dict[str, Any] | None = None


class HttpFilter:
    """요청 전후에 인증, 헤더, 로깅, 재시도 같은 공통 처리를 끼울 수 있는 확장점."""

    def before_request(self, request: HttpRequest) -> HttpRequest:
        """HTTP 요청을 보내기 전에 헤더나 payload를 보강할 기회를 제공한다."""

        return request

    def after_response(
        self,
        request: HttpRequest,
        response: httpx.Response,
    ) -> httpx.Response:
        """응답을 받은 뒤 상태 확인이나 후처리를 추가할 기회를 제공한다."""

        return response


class CallbackHttpFilter(HttpFilter):
    """간단한 실험성 필터를 클래스로 만들지 않고 콜백만으로 조립하게 한다."""

    def __init__(
        self,
        before: HttpRequestCallback | None = None,
        after: HttpResponseCallback | None = None,
    ) -> None:
        self.before = before
        self.after = after

    def before_request(self, request: HttpRequest) -> HttpRequest:
        if self.before is None:
            return request
        return self.before(request)

    def after_response(
        self,
        request: HttpRequest,
        response: httpx.Response,
    ) -> httpx.Response:
        if self.after is None:
            return response
        return self.after(request, response)


class UserAgentFilter(HttpFilter):
    """GitHub처럼 User-Agent를 요구하는 API에 기본 헤더를 자동으로 붙인다."""

    def __init__(self, user_agent: str) -> None:
        self.user_agent = user_agent

    def before_request(self, request: HttpRequest) -> HttpRequest:
        headers = dict(request.headers)
        headers.setdefault("User-Agent", self.user_agent)
        return replace(request, headers=headers)


class HttpClientPort(Protocol):
    def request_json(self, request: HttpRequest) -> Any: ...


class HttpClient:
    """프로젝트의 외부 HTTP 호출이 같은 필터 체인과 JSON 오류 처리를 쓰게 한다."""

    def __init__(self, filters: list[HttpFilter] | None = None) -> None:
        self.filters = filters or []

    def request_json(self, request: HttpRequest) -> Any:
        """필터 적용, 요청 실행, JSON 파싱, HTTP 오류 변환을 한 흐름으로 처리한다."""

        request = self.apply_before_filters(request)
        response = httpx.request(
            method=request.method,
            url=request.url,
            headers=request.headers,
            data=request.data,
            json=request.json,
            timeout=request.timeout,
        )
        response = self.apply_after_filters(request, response)
        return parse_json_response(response)

    def apply_before_filters(self, request: HttpRequest) -> HttpRequest:
        """등록된 필터 순서대로 요청 객체를 변환한다."""

        for http_filter in self.filters:
            request = http_filter.before_request(request)
        return request

    def apply_after_filters(
        self,
        request: HttpRequest,
        response: httpx.Response,
    ) -> httpx.Response:
        """등록된 필터 순서대로 응답 객체를 후처리한다."""

        for http_filter in self.filters:
            response = http_filter.after_response(request, response)
        return response


class HttpRequestError(ValueError):
    pass


class HttpJsonDecodeError(HttpRequestError):
    pass


class HttpStatusError(HttpRequestError):
    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self.payload = payload
        super().__init__(build_status_error_message(status_code, payload))


def parse_json_response(response: httpx.Response) -> Any:
    """외부 API 응답을 JSON으로 통일하고 실패 원인을 도메인에서 다루기 쉬운 예외로 바꾼다."""

    try:
        payload = response.json()
    except ValueError as exc:
        raise HttpJsonDecodeError("http response is not valid json") from exc

    if response.status_code >= 400:
        raise HttpStatusError(response.status_code, payload)

    return payload


def build_status_error_message(status_code: int, payload: Any) -> str:
    """외부 API가 제공한 message를 우선 사용해 디버깅 가능한 오류 문구를 만든다."""

    if isinstance(payload, dict) and payload.get("message"):
        return str(payload["message"])
    return f"http request failed with status {status_code}"
