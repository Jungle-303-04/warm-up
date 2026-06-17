"""노트북 채팅 서비스(임베딩 검색 기반).

질문을 임베딩해 ChunkStore에서 근거 청크를 검색하고, 그 위에서 답변을
생성한다(LLM answerer가 주입되면 LLM, 없으면 결정론적 요약). 인덱싱은 소스
생성 시 백그라운드로 미리 수행되므로, 채팅 시점에는 질의 임베딩 + 검색만 한다.

외부 키 없이 동작: 임베딩은 기본 deterministic, answerer는 기본 None.
근거(소스/청크)가 없으면 에러 대신 "근거 부족" 응답을 돌려준다.
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


@dataclass(frozen=True, slots=True)
class ChatCitation:
    source_id: str
    source_title: str
    path: str | None
    snippet: str

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
        title_by_source = {source.id: source.title for source in sources}
        source_by_id = {source.id: source for source in sources}

        # 이전 대화 기록 가져오기
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

            # 1) 질문 재구성 (Query Reformulation)
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

            if answer_plan.route == AnswerRoute.DIRECT:
                # 인사/대화 또는 (소스 없을 때) 일반 지식 → RAG 생략, 바로 답변.
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

                # 4) 계획된 쿼리들로 다중 검색 (단일/다중 모두 동일 경로)
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

                # 5) RRF로 다중 쿼리 결과를 병합·재랭킹.
                hits = combine_search_results(results_per_query, top_k=plan.top_k)
                # 6) 에이전트 도구(우리 인덱스에 묶인 인프로세스 도구) 준비 후 답변.
                hits = self._context_expander().expand(
                    notebook_id,
                    hits,
                    source_ids=search_source_ids,
                    file_paths=file_paths,
                )
                tools = self._build_tools(notebook_id, search_source_ids, file_paths)
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

        evidence = [
            TextChunk(
                source_id=hit.chunk.source_id,
                source_title=title_by_source.get(hit.chunk.source_id, hit.chunk.source_id),
                text=hit.chunk.text,
                path=hit.chunk.file_path,
            )
            for hit in hits
        ]
        citations = _dedupe_citations(
            [_citation_from_chunk(chunk, question) for chunk in evidence]
        )
        conflicts = resolve_conflicts(hits, source_by_id)
        if conflicts:
            return ChatResult(
                answer=format_conflict_answer(conflicts),
                citations=citations,
            )

        answer = self._answer(question, evidence, history, tools=tools)
        return ChatResult(answer=answer, citations=citations)

    def _build_tools(
        self,
        notebook_id: str,
        source_ids: list[str] | None,
        file_paths: list[str] | None,
    ) -> list | None:
        """채팅 에이전트용 인프로세스 도구(우리 인덱스에 묶임). 설정이 꺼져 있으면 None."""
        if not getattr(self.settings, "chat_use_tools", False):
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
                    # 도구가 있으면 에이전트 루프로 답변(answerer가 지원). 없으면 단발.
                    answer = self.answerer.answer(
                        question, evidence, history, tools=tools
                    ).strip()
                else:
                    answer = self.answerer(question, evidence).strip()
                if answer:
                    return answer
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
    )


def _citation_to_payload(citation: ChatCitation) -> dict:
    return {
        "source_id": citation.source_id,
        "source_title": citation.source_title,
        "path": citation.path,
        "snippet": citation.snippet,
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
    seen: set[tuple[str, str | None, str]] = set()
    deduped: list[ChatCitation] = []
    for citation in citations:
        key = (citation.source_id, citation.path, citation.snippet)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(citation)
    return deduped


def _fallback_answer(evidence: list[TextChunk]) -> str:
    lines = ["검색된 근거를 기준으로 답변하면 다음과 같습니다."]
    for index, chunk in enumerate(evidence[:3], start=1):
        where = chunk.path or chunk.source_title
        lines.append(f"{index}. {where}: {_snippet(chunk.text, set())}")
    lines.append("자세한 근거는 아래 출처를 확인하세요.")
    return "\n".join(lines)


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
