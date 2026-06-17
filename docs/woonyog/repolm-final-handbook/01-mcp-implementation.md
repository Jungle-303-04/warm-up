# MCP 구현과 사용법

## 1. MCP란 무엇인가

MCP(Model Context Protocol)는 AI 클라이언트가 외부 시스템의 기능을 "도구", "리소스", "프롬프트" 형태로 호출할 수 있게 하는 프로토콜이다.

RepoLM에서 MCP는 다음 역할을 맡는다.

- 외부 GitHub 검색이나 파일 읽기 같은 기능을 LLM tool calling 표준 형태로 노출한다.
- LangGraph 제안 생성기가 필요할 때 MCP 도구를 LangChain `StructuredTool`로 변환해 LLM에 붙인다.
- 현재 구현은 원격 HTTP MCP가 아니라, 같은 백엔드 프로세스 환경에서 `python -m app.mcp.server`를 stdio로 띄우는 로컬 MCP 서버 구조다.

## 2. MCP 서버 기본 문법

일반적인 Python MCP 서버는 아래처럼 작성한다.

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
async def hello(name: str) -> str:
    return f"Hello {name}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

라인별 의미:

- `FastMCP("my-server")`: MCP 서버 이름과 tool registry를 만든다.
- `@mcp.tool()`: 아래 함수를 MCP tool로 등록한다.
- 함수 인자 타입과 docstring은 클라이언트가 볼 수 있는 tool schema의 근거가 된다.
- `mcp.run(transport="stdio")`: 표준 입력/출력을 통해 MCP 클라이언트와 통신한다.

## 3. 현재 RepoLM MCP 서버

현재 구현 파일은 `backend/app/mcp/server.py`다.

```python
import base64
import os
import subprocess
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("RepoLM")

_MAX_FILE_CHARS = 4000
_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
```

라인별 의미:

- `base64`: GitHub Contents API가 base64로 돌려주는 파일 본문을 디코딩할 때 쓴다.
- `os`: `GITHUB_TOKEN` 환경변수를 읽는다.
- `subprocess`: 현재 워크스페이스의 git 상태를 조회한다.
- `Path`: 워크스페이스 루트와 파일 경로를 안전하게 계산한다.
- `httpx`: GitHub API 호출에 사용하는 비동기 HTTP 클라이언트다.
- `FastMCP`: Python MCP 서버 구현체다.
- `mcp = FastMCP("RepoLM")`: RepoLM 이름으로 tool registry를 만든다.
- `_MAX_FILE_CHARS`: LLM 프롬프트로 너무 긴 파일이 들어가지 않도록 자르는 상한이다.
- `_WORKSPACE_ROOT`: `backend/app/mcp/server.py`에서 세 단계 위로 올라가 프로젝트 루트를 찾는다.

### GitHub 공통 헤더

```python
def _github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "RepoLM-MCP-Server/1.0",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    return headers
```

라인별 의미:

- 함수 반환 타입은 `dict[str, str]`이다.
- `Accept`: GitHub REST API v3 JSON 응답을 요청한다.
- `User-Agent`: GitHub API 요구사항을 만족하고 호출 주체를 식별한다.
- `GITHUB_TOKEN`: 있으면 인증 헤더를 붙여 rate limit을 높인다.
- 토큰이 없으면 공개 API 범위 안에서 동작한다.

### 로컬 git 명령 실행

```python
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
```

라인별 의미:

- `*args`: `git status`, `git log` 같은 인자를 가변으로 받는다.
- `git -C <root>`: 어떤 위치에서 호출해도 워크스페이스 루트 기준으로 git 명령을 실행한다.
- `check=True`: git 명령 실패 시 예외를 발생시킨다.
- `capture_output=True`: stdout/stderr를 캡처한다.
- `text=True`: bytes가 아니라 문자열로 받는다.
- `timeout=5`: MCP tool 호출이 오래 걸려 LLM 루프를 막지 않게 한다.
- 예외는 빈 문자열로 흡수한다. MCP tool은 raw stack trace 대신 해석 가능한 결과를 돌려주는 편이 안전하다.

### tool: 현재 워크스페이스 요약

```python
@mcp.tool()
async def get_repolm_workspace_summary() -> str:
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
```

라인별 의미:

- `@mcp.tool()`: 이 함수를 MCP tool로 노출한다.
- `async def`: MCP 서버가 비동기 tool 호출을 처리할 수 있게 한다.
- `branch`: 현재 브랜치를 가져온다.
- `commit`: 최근 커밋의 짧은 SHA와 제목을 가져온다.
- `status`: 변경 파일 목록을 가져온다.
- 반환값은 markdown 문자열이다. LLM이 바로 읽기 쉽도록 제목, 목록, 상태 블록으로 정리한다.

### tool: 워크스페이스 파일 읽기

```python
@mcp.tool()
async def read_workspace_file(path: str) -> str:
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
```

라인별 의미:

- `path`: 워크스페이스 기준 상대 경로만 받는다.
- `resolve()`: `../` 같은 경로 우회를 정규화한다.
- `relative_to(_WORKSPACE_ROOT)`: 최종 경로가 워크스페이스 안인지 검사한다.
- 워크스페이스 밖이면 읽지 않는다. 이게 MCP 파일 도구의 핵심 보안 장치다.
- 파일이 없거나 바이너리이면 사용자 친화 메시지를 돌려준다.
- 긴 파일은 `_MAX_FILE_CHARS`로 자른다.
- 반환은 `# path` 제목을 포함해 LLM이 출처를 인식하기 쉽게 만든다.

### tool: GitHub 저장소 검색

```python
@mcp.tool()
async def search_github_repositories(query: str) -> str:
    url = f"https://api.github.com/search/repositories?q={query}&per_page=3"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=_github_headers())
```

주요 의미:

- `query`를 GitHub repository search API에 넣는다.
- `per_page=3`: LLM 컨텍스트를 줄이기 위해 상위 3개만 받는다.
- `timeout=10.0`: 네트워크가 멈춰도 MCP 루프를 막지 않는다.
- 상태 코드별로 인증 오류, rate limit, 기타 오류를 사람이 읽을 수 있는 문자열로 돌려준다.

### tool: GitHub 파일 읽기

```python
@mcp.tool()
async def read_repo_file(repo: str, path: str, ref: str = "") -> str:
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    if ref.strip():
        url += f"?ref={ref.strip()}"
```

주요 의미:

- `repo`: `owner/name` 형식이다.
- `path`: 저장소 내부 파일 경로다.
- `ref`: 브랜치, 태그, commit SHA를 선택적으로 지정한다.
- GitHub Contents API가 디렉터리를 돌려주면 파일 목록을 반환하고, 파일이면 base64 본문을 디코딩한다.

### tool: GitHub 코드 검색

```python
@mcp.tool()
async def search_repo_code(repo: str, query: str) -> str:
    url = f"https://api.github.com/search/code?q={query}+repo:{repo}&per_page=5"
```

주요 의미:

- `repo:` 한정자로 특정 저장소 내부만 검색한다.
- GitHub code search는 인증이 필요한 경우가 많으므로 401/403이면 `GITHUB_TOKEN` 안내를 돌려준다.
- 결과는 `path`와 `html_url`만 반환한다. LLM에 불필요한 raw payload를 노출하지 않는다.

## 4. MCP 클라이언트와 LangChain 도구 변환

구현 파일은 `backend/app/mcp/client.py`다.

```python
class MCPClient:
    def __init__(self, server_path: str = "app.mcp.server"):
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", server_path],
        )
```

라인별 의미:

- `server_path`: Python module path다. 기본값은 `app.mcp.server`.
- `sys.executable`: 현재 venv의 Python 바이너리를 그대로 쓴다.
- `python -m app.mcp.server`: MCP 서버를 stdio subprocess로 실행한다.

```python
async def list_tools_as_langchain(self) -> list[StructuredTool]:
    async with stdio_client(self.server_params) as (read, write), \
           ClientSession(read, write) as session:
        await session.initialize()
        mcp_tools = await session.list_tools()
        return [self._to_langchain_tool(tool) for tool in mcp_tools.tools]
```

라인별 의미:

- `stdio_client`: MCP 서버 subprocess와 read/write stream을 연결한다.
- `ClientSession`: MCP protocol session을 만든다.
- `initialize()`: tool list 호출 전 handshake다.
- `list_tools()`: 서버가 등록한 MCP tool 목록을 가져온다.
- `_to_langchain_tool`: MCP tool schema를 LangChain `StructuredTool`로 바꾼다.

```python
async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
    result = await session.call_tool(tool_name, arguments)
    texts = []
    for content in result.content:
        text = getattr(content, "text", None)
        if isinstance(text, str):
            texts.append(text)
    return "\n".join(texts)
```

라인별 의미:

- `call_tool`: LangGraph가 실행하라고 요청한 MCP tool을 실제로 호출한다.
- MCP 응답은 여러 content block일 수 있으므로 text block만 모은다.
- 반환은 문자열 하나로 합쳐 LLM의 `ToolMessage`에 넣는다.

```python
def _json_schema_to_pydantic(name: str, schema: dict) -> Any:
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    fields = {}
    for prop_name, prop_info in properties.items():
        prop_type = Any
        if prop_info.get("type") == "string":
            prop_type = str
        default = ... if prop_name in required else None
        fields[prop_name] = (prop_type, Field(default=default, description=desc))
    return create_model(f"{name}Schema", **fields)
```

라인별 의미:

- MCP tool은 JSON Schema로 인자를 설명한다.
- LangChain `StructuredTool`은 Pydantic args schema를 선호한다.
- 이 함수는 JSON Schema의 `properties`, `required`, `description`을 Pydantic 모델로 옮긴다.
- `default = ...`는 필수 필드를 의미한다.

## 5. 현재 RepoLM에서 MCP가 연결되는 위치

MCP는 `backend/app/pipeline/agent_graph.py`의 LangGraph proposer에서 사용된다.

```python
mcp_tools = await self.mcp_client.list_tools_as_langchain()
if mcp_tools and hasattr(self.chat_model, "bind_tools"):
    model_with_tools = self.chat_model.bind_tools(mcp_tools)
response = await model_with_tools.ainvoke(state["messages"])
```

동작 흐름:

1. LangGraph `agent` 노드가 MCP tool list를 조회한다.
2. Chat model이 `bind_tools`를 지원하면 MCP tool을 붙인다.
3. LLM이 tool call을 반환하면 `execute_tools` 노드가 `MCPClient.call_tool()`을 호출한다.
4. tool 결과가 `ToolMessage`로 메시지 목록에 추가된다.
5. 다시 `agent` 노드로 돌아가 최대 `max_steps`까지 반복한다.
6. 마지막에 `draft` 노드가 JSON proposal 목록을 만든다.

## 6. 실행 방법

로컬에서 MCP 서버만 실행:

```bash
cd backend
uv run python -m app.mcp.server
```

LangGraph 제안 그래프에서 사용:

```python
from app.mcp.client import MCPClient
from app.pipeline.agent_graph import LangGraphProposer

proposer = LangGraphProposer(
    chat_model=chat_model,
    mcp_client=MCPClient("app.mcp.server"),
)
drafts = proposer.generate(references, chunks)
```

GitHub API rate limit을 줄이고 싶을 때:

```bash
export GITHUB_TOKEN=github_pat_xxx
```

## 7. 할 수 있는 일과 한계

현재 MCP로 가능한 일:

- 현재 RepoLM 워크스페이스 상태 요약
- 워크스페이스 내부 텍스트 파일 읽기
- 공개 GitHub 저장소 검색
- GitHub 저장소 파일 읽기
- GitHub 저장소 코드 검색

현재 한계:

- 원격 Streamable HTTP MCP endpoint는 아직 없다.
- 노트북 채팅 본류는 MCP가 아니라 인프로세스 도구(`chat_tools.py`)를 사용한다.
- GitHub code search는 토큰이 없으면 실패할 수 있다.
- MCP 파일 읽기는 워크스페이스 내부로 제한된다.

