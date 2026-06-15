"""하이브리드 검색 점수 융합 (순수 로직).

키워드 점수와 벡터 점수를 각각 [0,1]로 정규화한 뒤 가중합한다.
    final = vector_weight * vector_norm + keyword_weight * keyword_norm
DB에 의존하지 않으므로 단위테스트로 검증한다.
"""

from dataclasses import dataclass

from app.pipeline.api.schemas import RetrievalChunk


@dataclass(slots=True)
class FusedScore:
    final: float
    vector_score: float
    keyword_score: float


@dataclass(slots=True)
class SearchHit:
    chunk: RetrievalChunk
    score: float
    vector_score: float
    keyword_score: float


def normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}

    lowest = min(scores.values())
    highest = max(scores.values())

    if highest == lowest:
        flat = 1.0 if highest > 0 else 0.0
        return {key: flat for key in scores}

    span = highest - lowest
    return {key: (value - lowest) / span for key, value in scores.items()}


def fuse_scores(
    vector_scores: dict[str, float],
    keyword_scores: dict[str, float],
    vector_weight: float,
    keyword_weight: float,
) -> dict[str, FusedScore]:
    vector_norm = normalize_scores(vector_scores)
    keyword_norm = normalize_scores(keyword_scores)
    candidate_ids = set(vector_scores) | set(keyword_scores)

    fused: dict[str, FusedScore] = {}
    for candidate_id in candidate_ids:
        fused[candidate_id] = FusedScore(
            final=(
                vector_weight * vector_norm.get(candidate_id, 0.0)
                + keyword_weight * keyword_norm.get(candidate_id, 0.0)
            ),
            vector_score=vector_scores.get(candidate_id, 0.0),
            keyword_score=keyword_scores.get(candidate_id, 0.0),
        )

    return fused


def rank_fused(fused: dict[str, FusedScore], limit: int) -> list[tuple[str, FusedScore]]:
    ranked = sorted(fused.items(), key=lambda item: item[1].final, reverse=True)
    return ranked[:limit]
