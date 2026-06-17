"""ChunkStore의 in-memory 구현(개발/테스트/단일 프로세스용).

검색은 임베딩이 있으면 코사인 유사도(numpy 없이 순수 파이썬 dot/norm)를,
없거나 점수가 0이면 키워드 부분일치를 폴백으로 사용한다. 임베딩이 L2 정규화돼
있다고 가정하지 않고 매번 norm으로 나눠 안전하게 계산한다.
"""

import math
import re
import threading

from app.notebooks.domain.chunk_records import ChunkSearchHit, NotebookChunk

_TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣_./-]+")


class InMemoryChunkStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._chunks: dict[str, NotebookChunk] = {}

    def add_many(self, chunks: list[NotebookChunk]) -> None:
        with self._lock:
            for chunk in chunks:
                self._chunks[chunk.id] = chunk

    def delete_by_source(self, source_id: str) -> None:
        with self._lock:
            for chunk_id in [
                cid
                for cid, chunk in self._chunks.items()
                if chunk.source_id == source_id
            ]:
                del self._chunks[chunk_id]

    def count_by_source(self, source_id: str) -> int:
        with self._lock:
            return sum(
                1 for chunk in self._chunks.values() if chunk.source_id == source_id
            )

    def get_many(
        self,
        notebook_id: str,
        chunk_ids: list[str],
        *,
        source_ids: list[str] | None = None,
        file_paths: list[str] | None = None,
    ) -> list[NotebookChunk]:
        wanted = set(chunk_ids)
        allowed_paths = set(file_paths) if file_paths is not None else None
        with self._lock:
            chunks = [
                chunk
                for chunk in self._chunks.values()
                if chunk.id in wanted
                and chunk.notebook_id == notebook_id
                and (source_ids is None or chunk.source_id in source_ids)
                and (
                    allowed_paths is None
                    or chunk.file_path is None
                    or chunk.file_path in allowed_paths
                )
            ]
        by_id = {chunk.id: chunk for chunk in chunks}
        return [by_id[chunk_id] for chunk_id in chunk_ids if chunk_id in by_id]

    def search(
        self,
        notebook_id: str,
        *,
        query_embedding: list[float] | None,
        query_text: str,
        source_ids: list[str] | None,
        top_k: int,
        file_paths: list[str] | None = None,
    ) -> list[ChunkSearchHit]:
        # file_paths가 주어지면 파일 단위 범위 필터: file_path가 없는(비repo 본문)
        # 청크는 항상 통과시키고, 경로가 있는(repo 파일) 청크는 선택된 경로만 후보로 둔다.
        allowed_paths = set(file_paths) if file_paths is not None else None
        with self._lock:
            candidates = [
                chunk
                for chunk in self._chunks.values()
                if chunk.notebook_id == notebook_id
                and (source_ids is None or chunk.source_id in source_ids)
                and (
                    allowed_paths is None
                    or chunk.file_path is None
                    or chunk.file_path in allowed_paths
                )
            ]

        query_tokens = _tokens(query_text)
        scored: list[tuple[float, int, ChunkSearchHit]] = []
        for index, chunk in enumerate(candidates):
            score = 0.0
            if query_embedding is not None and chunk.embedding is not None:
                score = _cosine(query_embedding, chunk.embedding)
            matched = _matched_terms(query_tokens, chunk)
            if score <= 0.0 and matched:
                # 임베딩이 없거나 의미 점수가 0이면 키워드 부분일치로 폴백.
                score = 0.001 * len(matched)
            if score <= 0.0:
                continue
            hit = ChunkSearchHit(chunk=chunk, score=score, matched_terms=matched)
            scored.append((score, index, hit))

        scored.sort(key=lambda item: (-item[0], item[1]))
        return [hit for _, _, hit in scored[:top_k]]


def _cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        return 0.0
    dot = 0.0
    left_norm = 0.0
    right_norm = 0.0
    for a, b in zip(left, right, strict=False):
        dot += a * b
        left_norm += a * a
        right_norm += b * b
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (math.sqrt(left_norm) * math.sqrt(right_norm))


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in _TOKEN_RE.findall(text)
        if len(token.strip("._/-")) >= 2
    }


def _matched_terms(query_tokens: set[str], chunk: NotebookChunk) -> list[str]:
    if not query_tokens:
        return []
    haystack = f"{chunk.file_path or ''} {chunk.text}".lower()
    return sorted(token for token in query_tokens if token in haystack)
