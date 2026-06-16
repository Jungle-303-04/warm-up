"""노트북 소스 기반 결정론적 채팅 서비스.

외부 LLM/임베딩 없이도 항상 동작하는 키워드 근거 검색을 기본 경로로 둔다.
선택적 answerer가 주입되면 검색된 근거 위에서 답변 문장만 대체할 수 있다.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.notebooks.domain.ports import NotebookStore
from app.notebooks.domain.records import ChatMessageRecord, SourceRecord

MAX_CHUNKS = 5
CHUNK_SIZE = 900
SNIPPET_SIZE = 360
TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣_./-]+")


@dataclass(frozen=True, slots=True)
class TextChunk:
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
    answerer: ChatAnswerer | None = None
    clock: Callable[[], datetime] = _utcnow
    id_factory: Callable[[], str] = _new_id

    def ask(
        self,
        notebook_id: str,
        *,
        question: str,
        source_ids: list[str] | None = None,
    ) -> ChatResult:
        normalized_question = question.strip()
        if not normalized_question:
            raise ValueError("question은 비어 있을 수 없습니다")

        self.store.get_notebook(notebook_id)  # 존재 확인
        sources = self.store.list_sources(notebook_id)
        selected = _select_sources(sources, source_ids)
        chunks = [chunk for source in selected for chunk in _chunks_from_source(source)]

        if not sources:
            result = ChatResult(
                answer="아직 연결된 소스가 없어 답변할 근거가 없습니다. 먼저 소스를 추가해 주세요.",
                citations=[],
            )
        elif not selected:
            result = ChatResult(
                answer=(
                    "선택된 소스가 없어 답변할 근거가 없습니다. "
                    "왼쪽 소스 패널에서 소스를 선택해 주세요."
                ),
                citations=[],
            )
        elif not chunks:
            result = ChatResult(
                answer="선택된 소스에서 읽을 수 있는 텍스트 근거를 찾지 못했습니다.",
                citations=[],
            )
        elif not (evidence := _rank_chunks(normalized_question, chunks)):
            result = ChatResult(
                answer=(
                    "선택된 소스에서 질문과 직접적으로 연결되는 근거를 찾지 못했습니다. "
                    "질문을 더 구체적으로 바꾸거나 관련 소스를 추가해 주세요."
                ),
                citations=[],
            )
        else:
            answer = self._answer(normalized_question, evidence)
            citations = [_citation_from_chunk(chunk, normalized_question) for chunk in evidence]
            result = ChatResult(answer=answer, citations=_dedupe_citations(citations))

        self._record_turn(notebook_id, normalized_question, result, source_ids)
        return result

    def list_messages(self, notebook_id: str) -> list[ChatMessageRecord]:
        return self.store.list_chat_messages(notebook_id)

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


def _chunks_from_source(source: SourceRecord) -> list[TextChunk]:
    if source.kind in ("md", "text", "pdf") and source.content:
        return [
            TextChunk(source_id=source.id, source_title=source.title, text=text)
            for text in _split_text(source.content)
        ]

    if source.kind == "url":
        text = "\n".join(part for part in [source.title, source.url] if part)
        if not text:
            return []
        return [TextChunk(source_id=source.id, source_title=source.title, text=text)]

    if source.kind == "repo" and source.repo_snapshot:
        chunks: list[TextChunk] = []
        for entry in source.repo_snapshot:
            path = str(entry.get("path") or "")
            content = entry.get("content")
            if not path or not isinstance(content, str) or not content.strip():
                continue
            chunks.extend(
                TextChunk(
                    source_id=source.id,
                    source_title=source.title,
                    path=path,
                    text=text,
                )
                for text in _split_text(content)
            )
        return chunks

    return []


def _split_text(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").strip()
    if not normalized:
        return []

    paragraphs = [part.strip() for part in re.split(r"\n{2,}", normalized) if part.strip()]
    chunks: list[str] = []
    for paragraph in paragraphs or [normalized]:
        if len(paragraph) <= CHUNK_SIZE:
            chunks.append(paragraph)
            continue
        for start in range(0, len(paragraph), CHUNK_SIZE):
            chunk = paragraph[start : start + CHUNK_SIZE].strip()
            if chunk:
                chunks.append(chunk)
    return chunks


def _rank_chunks(question: str, chunks: list[TextChunk]) -> list[TextChunk]:
    tokens = _tokens(question)
    if not tokens:
        return []

    scored = [
        (score, index, chunk)
        for index, chunk in enumerate(chunks)
        if (score := _score_chunk(tokens, chunk)) > 0
    ]
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [chunk for _, _, chunk in scored[:MAX_CHUNKS]]


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in TOKEN_RE.findall(text)
        if len(token.strip("._/-")) >= 2
    }


def _score_chunk(tokens: set[str], chunk: TextChunk) -> int:
    haystack = f"{chunk.source_title} {chunk.path or ''} {chunk.text}".lower()
    title_path = f"{chunk.source_title} {chunk.path or ''}".lower()
    score = 0
    for token in tokens:
        count = haystack.count(token)
        if count == 0:
            continue
        score += count
        if token in title_path:
            score += 2
    return score


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
    lines = ["선택된 소스에서 확인한 근거를 기준으로 답변하면 다음과 같습니다."]
    for index, chunk in enumerate(evidence[:3], start=1):
        where = chunk.path or chunk.source_title
        lines.append(f"{index}. {where}: {_snippet(chunk.text, set())}")
    lines.append("자세한 근거는 아래 출처를 확인하세요.")
    return "\n".join(lines)
