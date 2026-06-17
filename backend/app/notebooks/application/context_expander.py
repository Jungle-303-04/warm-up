"""검색 결과 컨텍스트 확장.

top chunk만 답변에 넣으면 근거 앞뒤 맥락이 부족해질 수 있다. 이 확장기는
청크 envelope의 parent/prev/next 링크를 사용해 같은 scope 안에서 주변 청크를
추가한다.
"""

from dataclasses import dataclass

from app.notebooks.domain.chunk_records import ChunkSearchHit
from app.notebooks.domain.ports import ChunkStore


@dataclass(frozen=True, slots=True)
class NeighborContextExpander:
    chunk_store: ChunkStore
    limit: int

    def expand(
        self,
        notebook_id: str,
        hits: list[ChunkSearchHit],
        *,
        source_ids: list[str] | None,
        file_paths: list[str] | None,
    ) -> list[ChunkSearchHit]:
        if not hits:
            return []

        seen = {hit.chunk.id for hit in hits}
        neighbor_ids: list[str] = []
        for hit in hits:
            for chunk_id in (
                hit.chunk.parent_chunk_id,
                hit.chunk.prev_chunk_id,
                hit.chunk.next_chunk_id,
            ):
                if chunk_id and chunk_id not in seen:
                    seen.add(chunk_id)
                    neighbor_ids.append(chunk_id)

        if not neighbor_ids:
            return hits[: self.limit]

        extra_chunks = self.chunk_store.get_many(
            notebook_id,
            neighbor_ids[: self.limit],
            source_ids=source_ids,
            file_paths=file_paths,
        )
        expanded = list(hits)
        expanded.extend(ChunkSearchHit(chunk=chunk, score=0.0) for chunk in extra_chunks)
        return expanded[: self.limit]
