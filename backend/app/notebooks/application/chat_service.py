"""노트북 채팅 서비스(임베딩 검색 기반).

질문을 임베딩해 ChunkStore에서 근거 청크를 검색하고, 그 위에서 답변을
생성한다(LLM answerer가 주입되면 LLM, 없으면 결정론적 요약). 인덱싱은 소스
생성 시 백그라운드로 미리 수행되므로, 채팅 시점에는 질의 임베딩 + 검색만 한다.

외부 키 없이 동작: 임베딩은 기본 deterministic, answerer는 기본 None.
근거(소스/청크)가 없으면 에러 대신 "근거 부족" 응답을 돌려준다.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.notebooks.domain.chunk_records import ChunkSearchHit
from app.notebooks.domain.ports import ChunkStore, NotebookStore
from app.notebooks.domain.records import ChatMessageRecord, SourceRecord
from app.repo_rag.domain.ports import EmbeddingClient

MAX_CHUNKS = 5
SNIPPET_SIZE = 360
TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣_./-]+")


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


@dataclass(frozen=True, slots=True)
class ChatResult:
    answer: str
    citations: list[ChatCitation]


ChatAnswerer = Callable[[str, list[TextChunk]], str]


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_id() -> str:
    return uuid4().hex


@dataclass(slots=True)
class ChatService:
    store: NotebookStore
    chunk_store: ChunkStore
    embedder: EmbeddingClient
    answerer: ChatAnswerer | None = None
    clock: Callable[[], datetime] = _utcnow
    id_factory: Callable[[], str] = _new_id

    def ask(
        self,
        notebook_id: str,
        *,
        question: str,
        source_ids: list[str] | None = None,
        file_paths: list[str] | None = None,
    ) -> ChatResult:
        normalized_question = question.strip()
        if not normalized_question:
            raise ValueError("question은 비어 있을 수 없습니다")

        self.store.get_notebook(notebook_id)  # 존재 확인(없으면 KeyError → 404)
        sources = self.store.list_sources(notebook_id)
        selected = _select_sources(sources, source_ids)
        title_by_source = {source.id: source.title for source in sources}

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
            query_embedding = self.embedder.embed_query(normalized_question)
            hits = self.chunk_store.search(
                notebook_id,
                query_embedding=query_embedding,
                query_text=normalized_question,
                source_ids=search_source_ids,
                top_k=MAX_CHUNKS,
                file_paths=file_paths,
            )
            result = self._result_from_hits(normalized_question, hits, title_by_source)

        self._record_turn(notebook_id, normalized_question, result, source_ids)
        return result

    def list_messages(self, notebook_id: str) -> list[ChatMessageRecord]:
        return self.store.list_chat_messages(notebook_id)

    def _result_from_hits(
        self,
        question: str,
        hits: list[ChunkSearchHit],
        title_by_source: dict[str, str],
    ) -> ChatResult:
        if not hits:
            return ChatResult(
                answer=(
                    "선택된 소스에서 질문과 직접적으로 연결되는 근거를 찾지 못했습니다. "
                    "질문을 더 구체적으로 바꾸거나 관련 소스를 추가해 주세요."
                ),
                citations=[],
            )

        evidence = [
            TextChunk(
                source_id=hit.chunk.source_id,
                source_title=title_by_source.get(hit.chunk.source_id, hit.chunk.source_id),
                text=hit.chunk.text,
                path=hit.chunk.file_path,
            )
            for hit in hits
        ]
        answer = self._answer(question, evidence)
        citations = _dedupe_citations(
            [_citation_from_chunk(chunk, question) for chunk in evidence]
        )
        return ChatResult(answer=answer, citations=citations)

    def _answer(self, question: str, evidence: list[TextChunk]) -> str:
        if self.answerer is not None:
            try:
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


def _select_sources(
    sources: list[SourceRecord],
    source_ids: list[str] | None,
) -> list[SourceRecord]:
    if source_ids is None:
        return sources
    requested = set(source_ids)
    return [source for source in sources if source.id in requested]


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
