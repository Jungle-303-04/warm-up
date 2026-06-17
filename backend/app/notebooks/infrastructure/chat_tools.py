"""채팅 에이전트용 인프로세스 도구(우리 서비스 데이터에 묶임).

MCP 서브프로세스나 외부 GitHub API가 아니라, 현재 요청의 노트북 컨텍스트
(store·chunk_store·embedder)를 클로저로 잡아 우리가 인덱싱한 데이터를 직접 다룬다.

도구(LLM이 선택·호출):
- 소스_파일_읽기(path): 노트북 repo 소스의 파일 원문을 그대로 읽는다(RAG 청크 잘림 없이).
- 코드_검색(query): 우리 인덱스(chunk_store)에서 의미·키워드로 검색해 상위 근거를 돌려준다.
- 심볼_찾기(name): 소스 본문에서 class/def 정의 위치를 찾는다.

모두 동기 함수라 답변기에서 별도 async 브리지 없이 곧바로 호출된다.
LLM에 노출되는 도구 이름/설명은 한국어다.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from langchain_core.tools import StructuredTool

if TYPE_CHECKING:
    from app.notebooks.domain.ports import ChunkStore, NotebookStore
    from app.repo_rag.domain.ports import EmbeddingClient

# 도구 응답 길이 상한(프롬프트 토큰 보호).
_MAX_FILE_CHARS = 6000
_MAX_HITS = 5
_MAX_SYMBOL_HITS = 20


def build_notebook_tools(
    *,
    notebook_id: str,
    store: NotebookStore,
    chunk_store: ChunkStore,
    embedder: EmbeddingClient,
    source_ids: list[str] | None,
) -> list[StructuredTool]:
    """현재 노트북에 묶인 인프로세스 도구 목록을 만든다(범위: 선택 소스).

    source_ids=None 이면 노트북의 모든 소스를 범위로 본다.
    """

    def _scoped_sources():
        sources = store.list_sources(notebook_id)
        if source_ids is None:
            return sources
        wanted = set(source_ids)
        return [s for s in sources if s.id in wanted]

    def _iter_repo_files():
        """범위 내 repo 소스의 (path, content) 전체를 순회한다."""
        for source in _scoped_sources():
            snapshot = getattr(source, "repo_snapshot", None)
            if source.kind == "repo" and snapshot:
                for entry in snapshot:
                    yield entry.get("path", ""), (entry.get("content") or "")

    def read_source_file(path: str) -> str:
        """노트북 소스에서 지정한 경로의 파일 원문을 읽는다."""
        target = path.strip()
        if not target:
            return "경로가 비어 있습니다."
        # 정확 일치 우선, 없으면 끝부분(파일명) 일치로 폴백.
        exact = None
        suffix = None
        for fpath, content in _iter_repo_files():
            if fpath == target:
                exact = (fpath, content)
                break
            if suffix is None and fpath.endswith("/" + target.lstrip("/")):
                suffix = (fpath, content)
        # repo 외 소스(md/text 등)도 content를 직접 노출.
        if exact is None and suffix is None:
            for source in _scoped_sources():
                if (
                    source.kind != "repo"
                    and getattr(source, "content", None)
                    and target.lower() in (source.title or "").lower()
                ):
                    exact = (source.title, source.content)
                    break
        hit = exact or suffix
        if hit is None:
            return f"'{path}' 파일을 노트북 소스에서 찾지 못했습니다."
        fpath, content = hit
        if len(content) > _MAX_FILE_CHARS:
            content = content[:_MAX_FILE_CHARS] + "\n...(이하 생략)"
        return f"# {fpath}\n{content}"

    def search_indexed_code(query: str) -> str:
        """인덱싱된 코드/문서에서 의미·키워드로 검색해 상위 근거를 돌려준다."""
        q = query.strip()
        if not q:
            return "검색어가 비어 있습니다."
        try:
            hits = chunk_store.search(
                notebook_id,
                query_embedding=embedder.embed_query(q),
                query_text=q,
                source_ids=source_ids,
                top_k=_MAX_HITS,
            )
        except Exception as e:
            return f"검색 중 오류: {e}"
        if not hits:
            return f"'{query}'에 대한 인덱스 결과가 없습니다."
        lines = []
        for hit in hits:
            where = hit.chunk.file_path or hit.chunk.source_id
            snippet = " ".join(hit.chunk.text.split())[:300]
            lines.append(f"[{where}] {snippet}")
        return "\n---\n".join(lines)

    def find_symbol(name: str) -> str:
        """소스 본문에서 class/def 등 심볼 정의 위치를 찾는다."""
        sym = name.strip()
        if not sym:
            return "심볼명이 비어 있습니다."
        pattern = re.compile(
            rf"^\s*(?:async\s+def|def|class)\s+{re.escape(sym)}\b", re.MULTILINE
        )
        results: list[str] = []
        for fpath, content in _iter_repo_files():
            for m in pattern.finditer(content):
                line_no = content.count("\n", 0, m.start()) + 1
                results.append(f"{fpath}:{line_no}  {m.group().strip()}")
                if len(results) >= _MAX_SYMBOL_HITS:
                    break
            if len(results) >= _MAX_SYMBOL_HITS:
                break
        if not results:
            return f"심볼 '{name}'의 정의를 찾지 못했습니다."
        return "정의 위치:\n" + "\n".join(results)

    # 도구 이름은 ASCII만 허용된다(OpenAI 함수콜 규칙: ^[a-zA-Z0-9_-]{1,64}$).
    # 따라서 name은 영문, 설명(description)만 한국어로 둔다.
    return [
        StructuredTool.from_function(
            func=read_source_file,
            name="read_source_file",
            description=(
                "노트북에 연결된 저장소 소스에서 지정한 경로의 파일 원문을 읽는다. "
                "RAG 청크로 잘리지 않은 전체 코드를 확인할 때 사용. 입력: path(파일 경로)."
            ),
        ),
        StructuredTool.from_function(
            func=search_indexed_code,
            name="search_indexed_code",
            description=(
                "이미 인덱싱된 코드/문서에서 의미·키워드로 관련 부분을 검색한다. "
                "어떤 파일에 무엇이 있는지 모를 때 먼저 사용. 입력: query(검색어)."
            ),
        ),
        StructuredTool.from_function(
            func=find_symbol,
            name="find_symbol",
            description=(
                "클래스/함수 등 심볼의 정의 위치(파일:라인)를 찾는다. "
                "특정 함수·클래스가 어디 정의됐는지 알 때 사용. 입력: name(심볼명)."
            ),
        ),
    ]
