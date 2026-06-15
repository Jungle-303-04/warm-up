from app.repo_rag.domain.retrieval import fuse_scores, normalize_scores, rank_fused


def test_normalize_minmax() -> None:
    normalized = normalize_scores({"a": 1.0, "b": 3.0, "c": 2.0})
    assert normalized["a"] == 0.0
    assert normalized["b"] == 1.0
    assert normalized["c"] == 0.5


def test_normalize_flat_scores() -> None:
    assert normalize_scores({"a": 2.0, "b": 2.0}) == {"a": 1.0, "b": 1.0}
    assert normalize_scores({"a": 0.0}) == {"a": 0.0}
    assert normalize_scores({}) == {}


def test_fuse_applies_weights() -> None:
    fused = fuse_scores({"a": 1.0, "b": 0.0}, {"a": 0.0, "b": 1.0}, 0.7, 0.3)
    assert abs(fused["a"].final - 0.7) < 1e-9
    assert abs(fused["b"].final - 0.3) < 1e-9
    assert fused["a"].vector_score == 1.0
    assert fused["b"].keyword_score == 1.0


def test_fuse_unions_candidates_with_zero_fill() -> None:
    fused = fuse_scores({"a": 1.0}, {"b": 1.0}, 0.7, 0.3)
    assert set(fused) == {"a", "b"}


def test_rank_respects_limit_and_order() -> None:
    fused = fuse_scores({"a": 1.0, "b": 0.5, "c": 0.0}, {}, 1.0, 0.0)
    ranked = rank_fused(fused, 2)
    assert [candidate_id for candidate_id, _ in ranked] == ["a", "b"]
