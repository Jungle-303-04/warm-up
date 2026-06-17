import base64
import os
import subprocess
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP

# MCP 서버 초기화
mcp = FastMCP("RepoLM")

# GitHub API 응답에서 파일 본문을 자를 상한(프롬프트 토큰 보호).
_MAX_FILE_CHARS = 4000
_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


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


def _git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(_WORKSPACE_ROOT), *args],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip()


@mcp.tool()
async def get_repolm_workspace_summary() -> str:
    """현재 RepoLM 워크스페이스의 브랜치, 최근 커밋, 주요 실행 명령을 요약한다."""
    branch = _git("rev-parse", "--abbrev-ref", "HEAD") or "unknown"
    commit = _git("log", "-1", "--pretty=format:%h %s") or "unknown"
    status = _git("status", "--short") or "(clean)"
    return "\n".join(
        [
            "# RepoLM workspace",
            f"- root: {_WORKSPACE_ROOT}",
            f"- branch: {branch}",
            f"- last_commit: {commit}",
            "- backend gates: cd backend && uv run pytest -q "
            "&& uv run pyright && uv run ruff check .",
            "- frontend gate: pnpm --filter @repolm/web typecheck",
            "",
            "## git status",
            status,
        ]
    )


@mcp.tool()
async def read_workspace_file(path: str) -> str:
    """RepoLM 워크스페이스 안의 텍스트 파일을 안전하게 읽는다.

    Args:
        path: 워크스페이스 기준 상대 경로(예: "backend/app/main.py").
    """
    try:
        target = (_WORKSPACE_ROOT / path).resolve()
        target.relative_to(_WORKSPACE_ROOT)
    except ValueError:
        return "오류: 워크스페이스 밖의 파일은 읽을 수 없습니다."
    if not target.is_file():
        return f"파일을 찾지 못했습니다: {path}"
    try:
        text = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"텍스트 파일이 아닙니다: {path}"
    except OSError as exc:
        return f"파일 읽기 중 오류: {exc!s}"
    if len(text) > _MAX_FILE_CHARS:
        text = text[:_MAX_FILE_CHARS] + "\n...(생략)"
    return f"# {path}\n{text}"


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
                # 디렉터리인 경우 항목 목록을 돌려줌
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
    # 코드 검색은 인증이 필요 q에 repo 한정자를 부여
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
