"""노트북 채팅 서비스(임베딩 검색 기반).

흐름:
- 질문 임베딩
- ChunkStore 근거 검색
- LLM answerer 또는 결정론 요약
- 근거 부족 응답

전제:
- 인덱싱은 소스 생성 시 백그라운드 처리
- 채팅 시점 작업은 질의 임베딩과 검색 중심
- 외부 키 없이 deterministic 임베딩과 answerer None 구성 가능
"""

import contextlib
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from app.config import Settings, get_settings
from app.notebooks.application.answer_planner import (
    AnswerPlanner,
    AnswerRoute,
    DeterministicAnswerPlanner,
)
from app.notebooks.application.context_expander import NeighborContextExpander
from app.notebooks.application.result_combiner import combine_search_results
from app.notebooks.application.service import DEFAULT_OWNER_USER_ID
from app.notebooks.application.trust import format_conflict_answer, resolve_conflicts
from app.notebooks.domain.chunk_records import ChunkSearchHit
from app.notebooks.domain.ports import ChunkStore, ContextExpander, NotebookStore
from app.notebooks.domain.records import ChatMessageRecord, SourceRecord
from app.notebooks.domain.source_evidence import (
    is_repo_code_source,
    is_repo_document_source,
)
from app.notebooks.domain.source_scope import select_sources
from app.repo_rag.domain.ports import EmbeddingClient

SNIPPET_SIZE = 360
TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣_./-]+")
CONTEXT_EXPANSION_LIMIT = 12
NO_EVIDENCE_ANSWER = "자료 내에서 확인할 수 있는 근거를 찾지 못했습니다."


@dataclass(frozen=True, slots=True)
class TextChunk:
    """answerer에 전달되는 근거 청크(LLM 컨텍스트 구성용)."""

    source_id: str
    source_title: str
    text: str
    path: str | None = None
    start_line: int | None = None
    end_line: int | None = None


@dataclass(frozen=True, slots=True)
class ChatCitation:
    source_id: str
    source_title: str
    path: str | None
    snippet: str
    start_line: int | None = None
    end_line: int | None = None

    @property
    def file_path(self) -> str | None:
        return self.path


@dataclass(frozen=True, slots=True)
class ChatResult:
    answer: str
    citations: list[ChatCitation]


ChatAnswerer = Callable[[str, list[TextChunk]], str]
CommitHistoryFetcher = Callable[[SourceRecord, int], list[dict]]


def get_clock() -> Callable[[], datetime]:
    return lambda: datetime.now(UTC)


def get_id_factory() -> Callable[[], str]:
    return lambda: uuid4().hex


@dataclass(slots=True)
class ChatService:
    store: NotebookStore
    chunk_store: ChunkStore
    embedder: EmbeddingClient
    answerer: ChatAnswerer | None = None
    settings: Settings = field(default_factory=get_settings)
    clock: Any = field(default_factory=get_clock)
    id_factory: Any = field(default_factory=get_id_factory)
    context_expander: ContextExpander | None = None
    commit_fetcher: CommitHistoryFetcher | None = None
    answer_planner: AnswerPlanner | None = None

    def ask(
        self,
        notebook_id: str,
        *,
        question: str,
        source_ids: list[str] | None = None,
        file_paths: list[str] | None = None,
        owner_user_id: int = DEFAULT_OWNER_USER_ID,
    ) -> ChatResult:
        normalized_question = question.strip()
        if not normalized_question:
            raise ValueError("question은 비어 있을 수 없습니다")

        self.store.get_notebook(notebook_id, owner_user_id=owner_user_id)
        sources = self.store.list_sources(notebook_id)
        selected = select_sources(sources, source_ids)
        title_by_source = _title_by_source_map(sources)
        source_by_id = {source.id: source for source in sources}

        # 이전 대화 기록
        chat_history = self.store.list_chat_messages(notebook_id)

        if not sources:
            result = ChatResult(
                answer="아직 연결된 소스가 없어 답변할 근거가 없습니다. 먼저 소스를 추가해 주세요.",
                citations=[],
            )
        elif source_ids is not None and not selected:
            result = ChatResult(
                answer=(
                    "선택된 소스가 없어 답변할 근거가 없습니다. "
                    "왼쪽 소스 패널에서 소스를 선택해 주세요."
                ),
                citations=[],
            )
        else:
            search_source_ids = (
                [source.id for source in selected] if source_ids is not None else None
            )

            # 1) 질문 재구성(Query Reformulation)
            standalone_question = normalized_question
            if chat_history and self.answerer and hasattr(self.answerer, "reformulate"):
                with contextlib.suppress(Exception):
                    standalone_question = self.answerer.reformulate(
                        normalized_question, chat_history
                    )

            has_sources = len(selected) > 0
            answer_plan = self._answer_planner().plan(
                standalone_question,
                has_sources=has_sources,
                source_count=len(selected),
            )

            if _should_ask_repo_scope(standalone_question, selected):
                result = _repo_scope_clarification_result(selected)
            elif answer_plan.route == AnswerRoute.DIRECT:
                # 인사/대화 또는 일반 지식 경로
                if self.answerer is not None:
                    answer = self._answer(normalized_question, [], chat_history)
                else:
                    answer = (
                        "안녕하세요! 연결된 소스에 대해 궁금한 점을 물어보시면 "
                        "근거와 함께 답변해 드릴게요."
                    )
                result = ChatResult(answer=answer, citations=[])
            elif answer_plan.route == AnswerRoute.COMMIT_HISTORY:
                result = self._commit_history_result(
                    selected,
                    owner_user_id=owner_user_id,
                )
            elif answer_plan.route == AnswerRoute.REPO_OVERVIEW:
                result = self._repo_overview_result(selected)
            elif answer_plan.search_plan is None:
                result = ChatResult(answer=NO_EVIDENCE_ANSWER, citations=[])
            else:
                plan = answer_plan.search_plan

                # 4) 계획 쿼리 기반 다중 검색
                results_per_query = [
                    self.chunk_store.search(
                        notebook_id,
                        query_embedding=self.embedder.embed_query(query),
                        query_text=query,
                        source_ids=search_source_ids,
                        top_k=plan.top_k,
                        file_paths=file_paths,
                    )
                    for query in plan.queries
                ]

                # 5) RRF 기반 결과 병합과 재랭킹
                hits = combine_search_results(results_per_query, top_k=plan.top_k)
                # 6) 인덱스 scope에 묶인 인프로세스 도구 준비
                hits = self._context_expander().expand(
                    notebook_id,
                    hits,
                    source_ids=search_source_ids,
                    file_paths=file_paths,
                )
                hits = _prioritize_source_code_hits(
                    standalone_question,
                    hits,
                    source_by_id,
                )
                tools = self._build_tools(
                    notebook_id,
                    search_source_ids,
                    file_paths,
                    preferred_tool_names=answer_plan.preferred_tools,
                )
                result = self._result_from_hits(
                    normalized_question,
                    hits,
                    title_by_source,
                    source_by_id,
                    chat_history,
                    tools=tools,
                )

        self._record_turn(notebook_id, normalized_question, result, source_ids)
        return result

    def list_messages(
        self,
        notebook_id: str,
        *,
        owner_user_id: int = DEFAULT_OWNER_USER_ID,
    ) -> list[ChatMessageRecord]:
        self.store.get_notebook(notebook_id, owner_user_id=owner_user_id)
        return self.store.list_chat_messages(notebook_id)

    def clear_messages(
        self,
        notebook_id: str,
        *,
        owner_user_id: int = DEFAULT_OWNER_USER_ID,
    ) -> None:
        self.store.get_notebook(notebook_id, owner_user_id=owner_user_id)
        self.store.clear_chat_messages(notebook_id)

    def _result_from_hits(
        self,
        question: str,
        hits: list[ChunkSearchHit],
        title_by_source: dict[str, str],
        source_by_id: dict[str, SourceRecord],
        history: list[ChatMessageRecord],
        tools: list | None = None,
    ) -> ChatResult:
        if not hits:
            return ChatResult(answer=NO_EVIDENCE_ANSWER, citations=[])

        hits = _dedupe_hits_for_context(hits)
        all_evidence = [
            TextChunk(
                source_id=hit.chunk.source_id,
                source_title=title_by_source.get(hit.chunk.source_id, hit.chunk.source_id),
                text=hit.chunk.text,
                path=hit.chunk.file_path,
                start_line=hit.chunk.start_line,
                end_line=hit.chunk.end_line,
            )
            for hit in hits
        ]
        all_citations = _dedupe_citations(
            [_citation_from_chunk(chunk, question) for chunk in all_evidence]
        )
        conflicts = resolve_conflicts(hits, source_by_id)
        if conflicts:
            return ChatResult(
                answer=format_conflict_answer(conflicts),
                citations=all_citations,
            )

        hits = _keep_repo_docs_only_when_aligned_with_code(
            question,
            hits,
            source_by_id,
        )
        hits = _dedupe_hits_for_context(hits)
        if not hits:
            return ChatResult(answer=NO_EVIDENCE_ANSWER, citations=[])

        evidence = [
            TextChunk(
                source_id=hit.chunk.source_id,
                source_title=title_by_source.get(hit.chunk.source_id, hit.chunk.source_id),
                text=hit.chunk.text,
                path=hit.chunk.file_path,
                start_line=hit.chunk.start_line,
                end_line=hit.chunk.end_line,
            )
            for hit in hits
        ]
        citations = _dedupe_citations(
            [_citation_from_chunk(chunk, question) for chunk in evidence]
        )

        answer = self._answer(question, evidence, history, tools=tools)
        return ChatResult(answer=answer, citations=citations)

    def _build_tools(
        self,
        notebook_id: str,
        source_ids: list[str] | None,
        file_paths: list[str] | None,
        *,
        preferred_tool_names: tuple[str, ...] = (),
    ) -> list | None:
        """채팅 에이전트용 인프로세스 도구 목록."""
        if not getattr(self.settings, "chat_use_tools", False):
            return None
        if not preferred_tool_names:
            return None
        try:
            from app.notebooks.infrastructure.chat_tools import build_notebook_tools

            return build_notebook_tools(
                notebook_id=notebook_id,
                store=self.store,
                chunk_store=self.chunk_store,
                embedder=self.embedder,
                source_ids=source_ids,
                file_paths=file_paths,
                tool_names=preferred_tool_names,
            )
        except Exception:
            return None

    def _commit_history_result(
        self,
        sources: list[SourceRecord],
        *,
        owner_user_id: int,
    ) -> ChatResult:
        repo_sources = [source for source in sources if source.kind == "repo"]
        if not repo_sources:
            return ChatResult(
                answer="선택된 소스 중 Git 저장소가 없어 커밋 이력을 확인할 수 없습니다.",
                citations=[],
            )

        facts: list[tuple[SourceRecord, dict]] = []
        for source in repo_sources:
            commits = list(source.repo_commits or [])
            if not commits and self.commit_fetcher is not None:
                commits = self.commit_fetcher(source, owner_user_id)
            for commit in commits[:5]:
                facts.append((source, commit))

        if not facts:
            return ChatResult(
                answer=(
                    "선택된 Git 저장소의 커밋 이력 메타데이터를 아직 확인하지 못했습니다. "
                    "소스를 재분석하면 최신 커밋 정보까지 함께 저장됩니다."
                ),
                citations=[],
            )

        lines = ["선택된 저장소 기준 최근 커밋 이력입니다."]
        citations: list[ChatCitation] = []
        for index, (source, commit) in enumerate(facts[:5], start=1):
            short_sha = str(commit.get("short_sha") or commit.get("sha") or "")[:12]
            message = str(commit.get("message") or "(메시지 없음)")
            author = str(commit.get("author_name") or "unknown")
            authored_at = str(commit.get("authored_at") or "date unknown")
            lines.append(
                f"{index}. `{short_sha}` {message} - {author}, {authored_at}"
            )
            citations.append(
                ChatCitation(
                    source_id=source.id,
                    source_title=source.title,
                    path=None,
                    snippet=f"{short_sha} {message}",
                )
            )
        return ChatResult(answer="\n".join(lines), citations=citations)

    def _repo_overview_result(self, sources: list[SourceRecord]) -> ChatResult:
        repo_sources = [source for source in sources if source.kind == "repo"]
        if not repo_sources:
            return ChatResult(
                answer="선택된 소스 중 Git 저장소가 없어 프로젝트 개요를 확인할 수 없습니다.",
                citations=[],
            )

        if len(repo_sources) == 1:
            lines = ["선택된 저장소 개요입니다."]
        else:
            lines = ["선택된 저장소가 여러 개라 각 저장소 기준으로 정리했습니다."]

        citations: list[ChatCitation] = []
        for index, source in enumerate(repo_sources, start=1):
            readme = _readme_entry(source.repo_snapshot)
            readme_title = None
            readme_summary = None
            if readme is not None:
                readme_title, readme_summary = _readme_overview(readme[1])
                citations.append(
                    ChatCitation(
                        source_id=source.id,
                        source_title=source.title,
                        path=readme[0],
                        snippet=_snippet(readme[1], set()),
                    )
                )

            display_title = readme_title or source.title
            branch = f" / branch `{source.branch}`" if source.branch else ""
            repo_url = f" ({source.repository_url})" if source.repository_url else ""
            file_count = len(source.repo_snapshot or [])
            lines.append(f"{index}. **{display_title}**{branch}{repo_url}")
            if readme_summary:
                lines.append(f"   - README 기준: {readme_summary}")
            if file_count:
                lines.append(f"   - 저장된 스냅샷 파일: {file_count}개")
            if not readme_summary and not file_count:
                lines.append("   - 저장된 README/파일 스냅샷이 없어 메타데이터만 확인됩니다.")

        if not citations:
            citations = [
                ChatCitation(
                    source_id=source.id,
                    source_title=source.title,
                    path=None,
                    snippet=source.repository_url or source.title,
                )
                for source in repo_sources
            ]
        return ChatResult(answer="\n".join(lines), citations=citations)

    def _context_expander(self) -> ContextExpander:
        if self.context_expander is not None:
            return self.context_expander
        return NeighborContextExpander(
            chunk_store=self.chunk_store,
            limit=CONTEXT_EXPANSION_LIMIT,
        )

    def _answer_planner(self) -> AnswerPlanner:
        if self.answer_planner is not None:
            return self.answer_planner
        return DeterministicAnswerPlanner(
            default_top_k=self.settings.chat_default_top_k,
            architecture_top_k=self.settings.chat_architecture_top_k,
        )

    def _answer(
        self,
        question: str,
        evidence: list[TextChunk],
        history: list[ChatMessageRecord],
        tools: list | None = None,
    ) -> str:
        if self.answerer is not None:
            try:
                if hasattr(self.answerer, "answer"):
                    # 도구 지원 answerer 경로
                    answer = self.answerer.answer(
                        question, evidence, history, tools=tools
                    ).strip()
                else:
                    answer = self.answerer(question, evidence).strip()
                if answer:
                    return _strip_inline_citation_markers(answer)
            except Exception:
                pass
        return _fallback_answer(evidence)

    def _record_turn(
        self,
        notebook_id: str,
        question: str,
        result: ChatResult,
        source_ids: list[str] | None,
    ) -> None:
        user_created_at = self.clock()
        self.store.add_chat_message(
            ChatMessageRecord(
                id=self.id_factory(),
                notebook_id=notebook_id,
                role="user",
                content=question,
                created_at=user_created_at,
                citations=[],
                source_ids=list(source_ids) if source_ids is not None else None,
            )
        )
        self.store.add_chat_message(
            ChatMessageRecord(
                id=self.id_factory(),
                notebook_id=notebook_id,
                role="assistant",
                content=result.answer,
                created_at=user_created_at + timedelta(microseconds=1),
                citations=[_citation_to_payload(citation) for citation in result.citations],
                source_ids=None,
            )
        )


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in TOKEN_RE.findall(text)
        if len(token.strip("._/-")) >= 2
    }


def _citation_from_chunk(chunk: TextChunk, question: str) -> ChatCitation:
    return ChatCitation(
        source_id=chunk.source_id,
        source_title=chunk.source_title,
        path=chunk.path,
        snippet=_snippet(chunk.text, _tokens(question)),
        start_line=chunk.start_line,
        end_line=chunk.end_line,
    )


def _citation_to_payload(citation: ChatCitation) -> dict:
    return {
        "source_id": citation.source_id,
        "source_title": citation.source_title,
        "path": citation.path,
        "snippet": citation.snippet,
        "start_line": citation.start_line,
        "end_line": citation.end_line,
    }


def _snippet(text: str, tokens: set[str]) -> str:
    compact = " ".join(text.split())
    if len(compact) <= SNIPPET_SIZE:
        return compact

    lowered = compact.lower()
    positions = [lowered.find(token) for token in tokens if lowered.find(token) >= 0]
    center = min(positions) if positions else 0
    start = max(0, center - SNIPPET_SIZE // 3)
    end = min(len(compact), start + SNIPPET_SIZE)
    snippet = compact[start:end].strip()
    if start > 0:
        snippet = f"...{snippet}"
    if end < len(compact):
        snippet = f"{snippet}..."
    return snippet


def _dedupe_citations(citations: list[ChatCitation]) -> list[ChatCitation]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[ChatCitation] = []
    for citation in citations:
        key = (
            citation.source_id,
            citation.path or "__source__",
            "" if citation.path else citation.snippet,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(citation)
    return deduped


def _dedupe_hits_for_context(hits: list[ChunkSearchHit]) -> list[ChunkSearchHit]:
    """LLM context precision용 청크/본문 단위 중복 제거."""
    seen: set[tuple[str, str | None, str]] = set()
    deduped: list[ChunkSearchHit] = []
    for hit in hits:
        key = (
            hit.chunk.source_id,
            hit.chunk.file_path,
            " ".join(hit.chunk.text.split()),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(hit)
    return deduped


_MULTI_REPO_SCOPE_KEYWORDS = (
    "이 레포",
    "이 저장소",
    "이 프로젝트",
    "레포",
    "저장소",
    "프로젝트",
    "코드",
    "구조",
    "아키텍처",
    "architecture",
    "구현",
    "기능",
    "커밋",
    "변경",
)

_MULTI_REPO_ALL_KEYWORDS = (
    "모든",
    "전체",
    "여러",
    "각각",
    "둘 다",
    "전부",
    "비교",
    "차이",
    "compare",
    "all",
    "each",
    "both",
)

_SOURCE_CODE_QUESTION_KEYWORDS = (
    "소스코드",
    "소스 코드",
    "코드",
    "구현",
    "로직",
    "함수",
    "메서드",
    "메소드",
    "클래스",
    "인터페이스",
    "타입",
    "api",
    "endpoint",
    "route",
    "router",
    "schema",
    "model",
    "service",
    "버그",
    "오류",
    "에러",
    "import",
    "export",
    "python",
    "typescript",
    "javascript",
    "fastapi",
    "next.js",
)

_CODE_ALIGNMENT_STOPWORDS = {
    "app",
    "src",
    "lib",
    "def",
    "class",
    "return",
    "self",
    "import",
    "from",
    "const",
    "let",
    "var",
    "function",
    "export",
    "default",
    "true",
    "false",
    "none",
    "null",
    "str",
    "int",
    "dict",
    "list",
}


def _title_by_source_map(sources: list[SourceRecord]) -> dict[str, str]:
    repo_key_counts: dict[str, int] = {}
    for source in sources:
        if source.kind == "repo" and source.repository_url:
            key = _repo_identity(source)
            repo_key_counts[key] = repo_key_counts.get(key, 0) + 1

    titles: dict[str, str] = {}
    for source in sources:
        title = source.title
        if (
            source.kind == "repo"
            and source.branch
            and source.repository_url
            and repo_key_counts.get(_repo_identity(source), 0) > 1
        ):
            title = f"{source.title} ({source.branch})"
        titles[source.id] = title
    return titles


def _should_ask_repo_scope(question: str, selected: list[SourceRecord]) -> bool:
    repo_sources = [source for source in selected if source.kind == "repo"]
    if len(repo_sources) < 2:
        return False
    if len({_repo_identity(source) for source in repo_sources}) <= 1:
        # 같은 저장소 여러 브랜치: branch별 답변 경로
        return False

    normalized = question.strip().lower()
    if any(keyword in normalized for keyword in _MULTI_REPO_ALL_KEYWORDS):
        return False
    if any(_mentions_source(normalized, source) for source in repo_sources):
        return False
    return any(keyword in normalized for keyword in _MULTI_REPO_SCOPE_KEYWORDS)


def _repo_scope_clarification_result(sources: list[SourceRecord]) -> ChatResult:
    repo_sources = [source for source in sources if source.kind == "repo"]
    options = [
        f"- {source.title}"
        + (f" / branch `{source.branch}`" if source.branch else "")
        for source in repo_sources[:6]
    ]
    extra = len(repo_sources) - len(options)
    if extra > 0:
        options.append(f"- 그 외 {extra}개 저장소")
    answer = (
        "여러 저장소가 선택되어 있어요. 어느 저장소를 기준으로 답변할지 알려주세요.\n"
        "여러 저장소를 함께 보려면 “전체 기준으로 비교해줘”처럼 말해주면 "
        "같이 묶어서 답하겠습니다.\n"
        + "\n".join(options)
    )
    return ChatResult(answer=answer, citations=[])


def _repo_identity(source: SourceRecord) -> str:
    value = source.repository_url or source.title
    return value.strip().rstrip("/").removesuffix(".git").lower()


def _mentions_source(question: str, source: SourceRecord) -> bool:
    candidates = {source.title.lower()}
    if source.repository_url:
        normalized_url = source.repository_url.rstrip("/").removesuffix(".git")
        candidates.add(normalized_url.lower())
        candidates.add(normalized_url.rsplit("/", maxsplit=1)[-1].lower())
    if source.branch:
        candidates.add(source.branch.lower())
    return any(candidate and candidate in question for candidate in candidates)


def _prioritize_source_code_hits(
    question: str,
    hits: list[ChunkSearchHit],
    source_by_id: dict[str, SourceRecord],
) -> list[ChunkSearchHit]:
    """소스코드 질문용 코드 근거 우선 정렬.

    기존 RAG 결과 유지, LLM/폴백 답변 evidence 순서만 조정.
    문서 청크는 코드 근거 뒤 보조 근거 위치.
    """
    if not _is_source_code_question(question):
        return hits
    if not any(_is_code_hit(hit, source_by_id) for hit in hits):
        return hits
    return sorted(
        hits,
        key=lambda hit: (
            _code_hit_priority(hit, source_by_id),
            _code_symbol_density(hit),
            hit.score,
        ),
        reverse=True,
    )


def _keep_repo_docs_only_when_aligned_with_code(
    question: str,
    hits: list[ChunkSearchHit],
    source_by_id: dict[str, SourceRecord],
) -> list[ChunkSearchHit]:
    """코드 질문용 repo docs/README 보조 근거 필터."""
    if not _is_source_code_question(question):
        return hits

    code_hits = [hit for hit in hits if _is_code_hit(hit, source_by_id)]
    if not code_hits:
        return hits

    code_terms = _code_alignment_terms(code_hits)
    if not code_terms:
        return hits

    filtered: list[ChunkSearchHit] = []
    for hit in hits:
        if not _is_repo_doc_hit(hit, source_by_id):
            filtered.append(hit)
            continue
        doc_terms = _tokens(f"{hit.chunk.file_path or ''} {hit.chunk.text}")
        if code_terms & doc_terms:
            filtered.append(hit)
    return filtered


def _code_alignment_terms(hits: list[ChunkSearchHit]) -> set[str]:
    terms: set[str] = set()
    for hit in hits:
        raw_terms = _tokens(f"{hit.chunk.file_path or ''} {hit.chunk.text}")
        terms.update(
            term
            for term in raw_terms
            if len(term.strip("._/-")) >= 3 and term not in _CODE_ALIGNMENT_STOPWORDS
        )
    return terms


def _is_repo_doc_hit(
    hit: ChunkSearchHit,
    source_by_id: dict[str, SourceRecord],
) -> bool:
    source = source_by_id.get(hit.chunk.source_id)
    if source is None:
        return False
    return is_repo_document_source(
        source,
        path=hit.chunk.file_path,
        language=hit.chunk.language,
    )


def _is_source_code_question(question: str) -> bool:
    normalized = question.strip().lower()
    return any(keyword in normalized for keyword in _SOURCE_CODE_QUESTION_KEYWORDS)


def _is_code_hit(
    hit: ChunkSearchHit,
    source_by_id: dict[str, SourceRecord],
) -> bool:
    source = source_by_id.get(hit.chunk.source_id)
    if source is None:
        return False
    return is_repo_code_source(
        source,
        path=hit.chunk.file_path,
        language=hit.chunk.language,
    )


def _code_hit_priority(
    hit: ChunkSearchHit,
    source_by_id: dict[str, SourceRecord],
) -> int:
    source = source_by_id.get(hit.chunk.source_id)
    if source is None:
        return 0
    path = (hit.chunk.file_path or "").lower()
    if is_repo_code_source(source, path=path, language=hit.chunk.language):
        return 100
    if _is_repo_doc_hit(hit, source_by_id):
        return -50
    if source.kind == "repo" and path:
        return 20
    return 0


def _code_symbol_density(hit: ChunkSearchHit) -> int:
    text = hit.chunk.text
    return (
        text.count("class ")
        + text.count("def ")
        + text.count("function ")
        + text.count("export ")
        + text.count("interface ")
        + text.count("@router")
        + text.count("APIRouter")
    )


def _fallback_answer(evidence: list[TextChunk]) -> str:
    lines = ["검색된 근거를 기준으로 답변하면 다음과 같습니다."]
    for index, chunk in enumerate(evidence[:3], start=1):
        where = chunk.path or chunk.source_title
        lines.append(f"{index}. {where}: {_snippet(chunk.text, set())}")
    lines.append("자세한 위치는 아래 근거 칩에서 파일과 라인을 확인하세요.")
    return "\n".join(lines)


INLINE_CITATION_MARKER_RE = re.compile(r"\s*\[(?:출처|근거)\s*\d+\]", re.IGNORECASE)


def _strip_inline_citation_markers(answer: str) -> str:
    """LLM 본문 내 번호형 출처 표기 제거.

    출처는 구조화된 citations 필드로 별도 전달.
    본문은 문장 내용 유지, 표식만 제거.
    """

    cleaned = INLINE_CITATION_MARKER_RE.sub("", answer)
    return re.sub(r"[ \t]+(\n|$)", r"\1", cleaned).strip()


def _readme_entry(snapshot: list[dict] | None) -> tuple[str, str] | None:
    for entry in snapshot or []:
        path = str(entry.get("path") or "")
        filename = path.lower().rsplit("/", maxsplit=1)[-1]
        content = entry.get("content")
        if filename.startswith("readme") and isinstance(content, str) and content.strip():
            return path, content
    return None


def _readme_overview(text: str) -> tuple[str | None, str | None]:
    title: str | None = None
    summary: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if title is None and line.startswith("#"):
            title = _clean_markdown_line(line)
            continue
        if summary is None and not line.startswith(("#", "!", "[!")):
            cleaned = _clean_markdown_line(line)
            if cleaned:
                summary = _snippet(cleaned, set())
                break
    return title, summary


def _clean_markdown_line(line: str) -> str:
    cleaned = re.sub(r"^#+\s*", "", line.strip())
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"[`*_>]+", "", cleaned)
    return " ".join(cleaned.split())
