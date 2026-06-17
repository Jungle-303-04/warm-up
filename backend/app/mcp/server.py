import base64
import os

import httpx
from mcp.server.fastmcp import FastMCP

# MCP 서버 초기화
mcp = FastMCP("SystemMCP")

# GitHub API 응답에서 파일 본문을 자를 상한(프롬프트 토큰 보호).
_MAX_FILE_CHARS = 4000


def _github_headers() -> dict[str, str]:
    """GitHub API 공통 헤더. GITHUB_TOKEN이 있으면 인증을 붙여 레이트리밋을 높인다."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "RepoLM-MCP-Server/1.0",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


@mcp.tool()
async def get_weather_forecast(city: str) -> str:
    """주어진 도시의 날씨 예보를 조회한다.

    Args:
        city: 도시 이름(예: "Seoul", "Tokyo", "London").
    """
    city_lower = city.strip().lower()
    if "seoul" in city_lower:
        return "Seoul: 24°C, Sunny, Humidity 45%, Wind 5km/h."
    elif "tokyo" in city_lower:
        return "Tokyo: 26°C, Partly Cloudy, Humidity 50%, Wind 7km/h."
    elif "london" in city_lower:
        return "London: 18°C, Light Rain, Humidity 80%, Wind 12km/h."
    else:
        return f"{city}: 20°C, Clear Sky, Humidity 55%, Wind 8km/h. (Mocked)"


@mcp.tool()
async def search_github_repositories(query: str) -> str:
    """검색어로 공개 GitHub 저장소를 검색한다.

    Args:
        query: 검색어(예: "langchain python", "fastapi react").
    """
    url = f"https://api.github.com/search/repositories?q={query}&per_page=3"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=_github_headers())

            if response.status_code == 401:
                return "Error: Unauthorized. The provided GITHUB_TOKEN is invalid."
            elif response.status_code == 403:
                return (
                    "Error: Rate limit exceeded or forbidden. "
                    "Try setting a GITHUB_TOKEN to increase limits."
                )
            elif response.status_code != 200:
                return (
                    f"Error: GitHub API returned status code {response.status_code} "
                    f"with detail: {response.text}"
                )

            data = response.json()
            items = data.get("items", [])
            if not items:
                return f"No GitHub repositories found for query: '{query}'"

            results = []
            for item in items:
                # 민감 정보 차단을 위해 필요한 정보만 필터링하여 프롬프트 정제 데이터로 반환
                results.append(
                    f"Name: {item.get('full_name')}\n"
                    f"Description: {item.get('description') or 'No description'}\n"
                    f"Stars: {item.get('stargazers_count')}\n"
                    f"URL: {item.get('html_url')}"
                )
            return "\n---\n".join(results)
    except Exception as e:
        return f"Error occurred during GitHub search: {e!s}"


@mcp.tool()
async def read_repo_file(repo: str, path: str, ref: str = "") -> str:
    """GitHub 저장소의 특정 파일 내용을 읽어 온다(코드 근거 확인용).

    Args:
        repo: "owner/name" 형식의 저장소(예: "fastapi/fastapi").
        path: 저장소 기준 파일 경로(예: "app/main.py").
        ref: 선택. 브랜치/태그/커밋 SHA. 비우면 기본 브랜치.
    """
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    if ref.strip():
        url += f"?ref={ref.strip()}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=_github_headers())
            if response.status_code == 404:
                return f"파일을 찾지 못했습니다: {repo}/{path}"
            if response.status_code == 403:
                return "오류: 레이트리밋/권한 문제. GITHUB_TOKEN 설정을 권장합니다."
            if response.status_code != 200:
                return f"오류: GitHub API 상태 코드 {response.status_code}"

            data = response.json()
            if isinstance(data, list):
                # 디렉터리인 경우 항목 목록을 돌려준다.
                names = [entry.get("path", "") for entry in data]
                return "디렉터리 항목:\n" + "\n".join(names)

            content = data.get("content", "")
            if data.get("encoding") == "base64" and content:
                text = base64.b64decode(content).decode("utf-8", errors="replace")
            else:
                text = content
            if len(text) > _MAX_FILE_CHARS:
                text = text[:_MAX_FILE_CHARS] + "\n...(생략)"
            return f"# {repo}/{path}\n{text}"
    except Exception as e:
        return f"파일 읽기 중 오류: {e!s}"


@mcp.tool()
async def search_repo_code(repo: str, query: str) -> str:
    """GitHub 저장소 안에서 코드/심볼을 검색한다(함수·클래스·문자열 위치 찾기).

    Args:
        repo: "owner/name" 형식의 저장소(예: "fastapi/fastapi").
        query: 검색할 코드 조각·심볼명(예: "class ChatService", "parse_config").
    """
    # 코드 검색은 인증이 필요하다. q에 repo 한정자를 붙인다.
    url = f"https://api.github.com/search/code?q={query}+repo:{repo}&per_page=5"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=_github_headers())
            if response.status_code in (401, 403):
                return (
                    "오류: 코드 검색은 인증이 필요합니다. GITHUB_TOKEN을 설정하세요 "
                    "(레이트리밋/권한)."
                )
            if response.status_code == 422:
                return f"검색어를 처리할 수 없습니다: '{query}'"
            if response.status_code != 200:
                return f"오류: GitHub API 상태 코드 {response.status_code}"

            items = response.json().get("items", [])
            if not items:
                return f"'{query}'에 대한 코드 결과가 없습니다(repo: {repo})."
            lines = [f"- {item.get('path')} ({item.get('html_url')})" for item in items]
            return "코드 검색 결과:\n" + "\n".join(lines)
    except Exception as e:
        return f"코드 검색 중 오류: {e!s}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
