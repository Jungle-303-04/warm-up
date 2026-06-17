"""다중 쿼리 검색 결과 병합 모듈.

여러 쿼리에서 나온 검색 결과 리스트를 Reciprocal Rank Fusion (RRF) 알고리즘으로
병합·재랭킹한다. 청크 id 기준으로 중복을 제거하며, 최종 top_k 개를 반환한다.

RRF 상수 k=60은 원래 논문(Cormack et al., 2009)의 기본값이다.
"""

from app.notebooks.domain.chunk_records import ChunkSearchHit

_RRF_K = 60


def combine_search_results(
    results_per_query: list[list[ChunkSearchHit]],
    top_k: int,
) -> list[ChunkSearchHit]:
    """다중 쿼리 결과를 RRF로 병합하여 top_k 개를 반환한다.

    Parameters
    ----------
    results_per_query:
        각 쿼리별 ChunkSearchHit 리스트. 내부 리스트는 점수 내림차순이어야 한다.
    top_k:
        최종 반환할 최대 결과 수.

    Returns
    -------
    list[ChunkSearchHit]
        RRF 점수 내림차순으로 정렬된 병합 결과(최대 top_k 개).
    """
    if not results_per_query:
        return []

    # 결과가 단 하나뿐이면 RRF 없이 바로 반환
    if len(results_per_query) == 1:
        return _dedupe_by_chunk_id(results_per_query[0])[:top_k]

    # RRF 점수 집계: chunk_id → (rrf_score, 최고 원본 hit)
    rrf_scores: dict[str, float] = {}
    best_hits: dict[str, ChunkSearchHit] = {}

    for result_list in results_per_query:
        for rank, hit in enumerate(result_list):
            chunk_id = hit.chunk.id
            rrf_score = 1.0 / (rank + _RRF_K)
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + rrf_score

            # 같은 chunk가 여러 쿼리에서 나왔으면 원본 점수가 높은 hit를 보존
            existing = best_hits.get(chunk_id)
            if existing is None or hit.score > existing.score:
                best_hits[chunk_id] = hit

    # RRF 점수로 재정렬
    ranked_ids = sorted(rrf_scores, key=lambda cid: rrf_scores[cid], reverse=True)

    results: list[ChunkSearchHit] = []
    for chunk_id in ranked_ids[:top_k]:
        original = best_hits[chunk_id]
        # RRF 점수를 score 필드에 반영한 새 hit 생성
        results.append(
            ChunkSearchHit(
                chunk=original.chunk,
                score=rrf_scores[chunk_id],
                matched_terms=original.matched_terms,
            )
        )

    return results


def _dedupe_by_chunk_id(hits: list[ChunkSearchHit]) -> list[ChunkSearchHit]:
    """chunk id 기준으로 중복 제거(먼저 나온 것 유지)."""
    seen: set[str] = set()
    deduped: list[ChunkSearchHit] = []
    for hit in hits:
        if hit.chunk.id not in seen:
            seen.add(hit.chunk.id)
            deduped.append(hit)
    return deduped
