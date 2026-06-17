"""ResultCombiner 단위 테스트.

combine_search_results()의 RRF 병합, 중복 제거, 랭킹이 올바른지 검증한다.
"""

from app.notebooks.application.result_combiner import combine_search_results
from app.notebooks.domain.chunk_records import ChunkSearchHit, NotebookChunk

# ================================================================== #
#  헬퍼
# ================================================================== #


def _make_chunk(chunk_id: str, text: str = "dummy") -> NotebookChunk:
    """테스트용 청크를 생성한다."""
    return NotebookChunk(
        id=chunk_id,
        notebook_id="nb1",
        source_id="src1",
        chunk_index=0,
        text=text,
    )


def _make_hit(chunk_id: str, score: float, matched_terms: list[str] | None = None) -> ChunkSearchHit:
    """테스트용 검색 결과를 생성한다."""
    return ChunkSearchHit(
        chunk=_make_chunk(chunk_id),
        score=score,
        matched_terms=matched_terms or [],
    )


# ================================================================== #
#  빈 입력 테스트
# ================================================================== #


class TestEmptyInputs:
    """빈 입력에 대한 처리를 테스트한다."""

    def test_empty_list(self):
        result = combine_search_results([], top_k=5)
        assert result == []

    def test_single_empty_result_list(self):
        result = combine_search_results([[]], top_k=5)
        assert result == []

    def test_multiple_empty_result_lists(self):
        result = combine_search_results([[], [], []], top_k=5)
        assert result == []


# ================================================================== #
#  단일 쿼리 결과 (RRF 불필요) 테스트
# ================================================================== #


class TestSingleQuery:
    """단일 쿼리 결과가 그대로 반환되는지 테스트한다."""

    def test_passthrough(self):
        hits = [_make_hit("c1", 0.9), _make_hit("c2", 0.7), _make_hit("c3", 0.5)]
        result = combine_search_results([hits], top_k=5)
        assert len(result) == 3
        assert result[0].chunk.id == "c1"
        assert result[1].chunk.id == "c2"
        assert result[2].chunk.id == "c3"

    def test_top_k_limits(self):
        hits = [_make_hit(f"c{i}", 1.0 - i * 0.1) for i in range(10)]
        result = combine_search_results([hits], top_k=3)
        assert len(result) == 3

    def test_dedup_in_single_query(self):
        hits = [_make_hit("c1", 0.9), _make_hit("c1", 0.8), _make_hit("c2", 0.7)]
        result = combine_search_results([hits], top_k=5)
        assert len(result) == 2
        ids = [hit.chunk.id for hit in result]
        assert ids == ["c1", "c2"]


# ================================================================== #
#  RRF 병합 테스트
# ================================================================== #


class TestRRFMerging:
    """다중 쿼리 RRF 병합이 올바르게 동작하는지 테스트한다."""

    def test_chunk_appearing_in_multiple_queries_ranks_higher(self):
        """양쪽 쿼리에 모두 등장한 청크가 하나에만 등장한 청크보다 높은 순위."""
        query1 = [_make_hit("c1", 0.9), _make_hit("c2", 0.8)]
        query2 = [_make_hit("c1", 0.7), _make_hit("c3", 0.6)]
        result = combine_search_results([query1, query2], top_k=5)
        assert result[0].chunk.id == "c1"

    def test_rrf_score_is_sum(self):
        """RRF 점수가 각 쿼리에서의 역순위 합인지 확인한다."""
        k = 60  # RRF 상수
        query1 = [_make_hit("c1", 0.9)]  # rank 0 → 1/(0+60) = 1/60
        query2 = [_make_hit("c1", 0.7)]  # rank 0 → 1/(0+60) = 1/60
        result = combine_search_results([query1, query2], top_k=5)
        expected_score = 1.0 / (0 + k) + 1.0 / (0 + k)
        assert abs(result[0].score - expected_score) < 1e-10

    def test_rank_matters_in_rrf(self):
        """낮은 순위(rank가 큰)일수록 RRF 기여가 작다."""
        k = 60
        # c1: query1에서 rank 0, c2: query1에서 rank 1
        # c1: query2에서 없음, c2: query2에서 rank 0
        query1 = [_make_hit("c1", 0.9), _make_hit("c2", 0.8)]
        query2 = [_make_hit("c2", 0.7)]
        result = combine_search_results([query1, query2], top_k=5)

        c1_rrf = 1.0 / (0 + k)
        c2_rrf = 1.0 / (1 + k) + 1.0 / (0 + k)
        # c2의 RRF 점수가 c1보다 높아야 한다
        assert c2_rrf > c1_rrf
        assert result[0].chunk.id == "c2"

    def test_three_queries_merge(self):
        """3개 쿼리 결과 병합."""
        q1 = [_make_hit("c1", 0.9), _make_hit("c2", 0.7)]
        q2 = [_make_hit("c2", 0.8), _make_hit("c3", 0.6)]
        q3 = [_make_hit("c2", 0.5), _make_hit("c1", 0.4)]
        result = combine_search_results([q1, q2, q3], top_k=5)
        # c2가 3개 쿼리 모두에 등장하므로 1위
        assert result[0].chunk.id == "c2"


# ================================================================== #
#  중복 제거 테스트
# ================================================================== #


class TestDeduplication:
    """RRF 병합 시 chunk id 기준 중복이 제거되는지 테스트한다."""

    def test_same_chunk_different_queries(self):
        q1 = [_make_hit("c1", 0.9), _make_hit("c2", 0.7)]
        q2 = [_make_hit("c1", 0.85), _make_hit("c2", 0.6)]
        result = combine_search_results([q1, q2], top_k=5)
        ids = [hit.chunk.id for hit in result]
        assert len(ids) == len(set(ids))

    def test_best_original_score_preserved(self):
        """같은 chunk가 여러 쿼리에 나올 때 가장 높은 원본 점수의 matched_terms가 보존되는지 확인."""
        hit_high = ChunkSearchHit(
            chunk=_make_chunk("c1"),
            score=0.95,
            matched_terms=["find_user"],
        )
        hit_low = ChunkSearchHit(
            chunk=_make_chunk("c1"),
            score=0.5,
            matched_terms=["user"],
        )
        result = combine_search_results([[hit_high], [hit_low]], top_k=5)
        assert result[0].matched_terms == ["find_user"]


# ================================================================== #
#  top_k 제한 테스트
# ================================================================== #


class TestTopKLimit:
    """top_k가 결과 수를 제한하는지 테스트한다."""

    def test_limits_output(self):
        q1 = [_make_hit(f"c{i}", 1.0 - i * 0.1) for i in range(5)]
        q2 = [_make_hit(f"d{i}", 0.9 - i * 0.1) for i in range(5)]
        result = combine_search_results([q1, q2], top_k=3)
        assert len(result) == 3

    def test_top_k_zero(self):
        q1 = [_make_hit("c1", 0.9)]
        result = combine_search_results([q1], top_k=0)
        assert result == []


# ================================================================== #
#  결과 순서 테스트
# ================================================================== #


class TestResultOrdering:
    """결과가 RRF 점수 내림차순인지 테스트한다."""

    def test_descending_rrf_score(self):
        q1 = [_make_hit("c1", 0.9), _make_hit("c2", 0.7), _make_hit("c3", 0.5)]
        q2 = [_make_hit("c3", 0.8), _make_hit("c1", 0.6)]
        result = combine_search_results([q1, q2], top_k=5)
        for i in range(len(result) - 1):
            assert result[i].score >= result[i + 1].score

    def test_rrf_scores_are_positive(self):
        q1 = [_make_hit("c1", 0.9)]
        q2 = [_make_hit("c2", 0.8)]
        result = combine_search_results([q1, q2], top_k=5)
        for hit in result:
            assert hit.score > 0
