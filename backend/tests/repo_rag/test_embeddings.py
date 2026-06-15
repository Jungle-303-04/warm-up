from app.repo_rag.infrastructure.embeddings import (
    DeterministicEmbeddingClient,
    OpenAIEmbeddingClient,
    _batches,
)


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def test_same_text_yields_same_vector() -> None:
    client = DeterministicEmbeddingClient(dimension=64)
    assert client.embed_query("def login(): return token") == client.embed_query(
        "def login(): return token"
    )


def test_vector_dimension_and_normalization() -> None:
    client = DeterministicEmbeddingClient(dimension=128)
    vector = client.embed_query("hello world")
    assert len(vector) == 128
    assert abs(sum(value * value for value in vector) ** 0.5 - 1.0) < 1e-9


def test_similar_texts_score_higher_than_dissimilar() -> None:
    client = DeterministicEmbeddingClient(dimension=512)
    base = client.embed_query("authentication login token jwt")
    near = client.embed_query("authentication login token session")
    far = client.embed_query("pandas dataframe numpy array plot")
    assert _cosine(base, near) > _cosine(base, far)


def test_embed_documents_returns_batch() -> None:
    client = DeterministicEmbeddingClient(dimension=32)
    vectors = client.embed_documents(["a b c", "d e f"])
    assert len(vectors) == 2
    assert all(len(vector) == 32 for vector in vectors)


def test_empty_text_returns_zero_vector() -> None:
    client = DeterministicEmbeddingClient(dimension=16)
    assert client.embed_query("") == [0.0] * 16


def test_batches_splits_evenly() -> None:
    assert list(_batches([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]
    assert list(_batches([], 2)) == []


class _FakeOpenAI:
    def __init__(self, fail_times: int = 0) -> None:
        self.fail_times = fail_times
        self.calls = 0

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("rate limited")
        return [[float(len(text))] for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text))]


def test_openai_client_batches_documents() -> None:
    fake = _FakeOpenAI()
    client = OpenAIEmbeddingClient(batch_size=2, client=fake)

    vectors = client.embed_documents(["a", "bb", "ccc", "dddd", "eeeee"])

    assert [v[0] for v in vectors] == [1.0, 2.0, 3.0, 4.0, 5.0]
    assert fake.calls == 3  # 2 + 2 + 1 배치


def test_openai_client_retries_transient_errors() -> None:
    fake = _FakeOpenAI(fail_times=2)
    client = OpenAIEmbeddingClient(batch_size=10, max_attempts=3, client=fake)

    vectors = client.embed_documents(["a", "bb"])

    assert [v[0] for v in vectors] == [1.0, 2.0]
    assert fake.calls == 3  # 2번 실패 후 성공
