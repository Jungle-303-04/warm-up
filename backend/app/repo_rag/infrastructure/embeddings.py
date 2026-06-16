"""임베딩 어댑터.

- `DeterministicEmbeddingClient`: 외부 API/키 없이 동작하는 해시 기반 임베딩(오프라인/테스트).
- `OpenAIEmbeddingClient`: langchain-openai 기반 실제 임베딩.
  - 대량 텍스트를 배치로 나눠 호출(EMBEDDING_BATCH_SIZE).
  - 일시 오류/레이트리밋에 tenacity 지수 백오프 재시도.
  - import는 지연시켜 패키지가 없어도 모듈 로딩이 깨지지 않는다.
"""

import math
import re
from collections.abc import Iterator, Sequence
from hashlib import sha256
from typing import Any

import tenacity

DEFAULT_OPENAI_MODEL = "text-embedding-3-small"
OPENAI_MODEL_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}
DETERMINISTIC_MODEL = "deterministic-hash"
DEFAULT_DETERMINISTIC_DIMENSION = 1536
EMBEDDING_BATCH_SIZE = 96
DEFAULT_MAX_ATTEMPTS = 3
_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")


class DeterministicEmbeddingClient:
    def __init__(self, dimension: int = DEFAULT_DETERMINISTIC_DIMENSION) -> None:
        self._dimension = dimension

    @property
    def model(self) -> str:
        return DETERMINISTIC_MODEL

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self._dimension
        for token in _tokenize(text):
            digest = sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self._dimension
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign
        return _l2_normalize(vector)


class OpenAIEmbeddingClient:
    def __init__(
        self,
        model: str = DEFAULT_OPENAI_MODEL,
        dimension: int | None = None,
        api_key: str | None = None,
        *,
        batch_size: int = EMBEDDING_BATCH_SIZE,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        client: object | None = None,
    ) -> None:
        self._model = model
        self._dimension = dimension or OPENAI_MODEL_DIMENSIONS.get(model, 1536)
        self._api_key = api_key
        self._batch_size = batch_size
        self._max_attempts = max_attempts
        self._client = client  # 주입되면 그대로 사용(테스트 시드)

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for batch in _batches(texts, self._batch_size):
            vectors.extend(self._retry(self._ensure_client().embed_documents, batch))  # type: ignore
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self._retry(self._ensure_client().embed_query, text)  # type: ignore

    def _retry(self, func, *args):
        retrying = tenacity.Retrying(
            stop=tenacity.stop_after_attempt(self._max_attempts),
            wait=tenacity.wait_exponential(multiplier=1, max=10),
            retry=tenacity.retry_if_exception_type(Exception),
            reraise=True,
        )
        return retrying(func, *args)

    def _ensure_client(self) -> object:
        if self._client is None:
            try:
                from langchain_openai import OpenAIEmbeddings  # type: ignore
            except ImportError as exc:  # pragma: no cover - 의존성 미설치 환경
                raise RuntimeError("OpenAI 임베딩을 쓰려면 langchain-openai가 필요합니다") from exc

            kwargs: dict[str, Any] = {"model": self._model}
            if self._api_key:
                kwargs["api_key"] = self._api_key
            self._client = OpenAIEmbeddings(**kwargs)  # type: ignore

        return self._client


def _batches(items: Sequence, size: int) -> Iterator[list]:
    for start in range(0, len(items), size):
        yield list(items[start : start + size])


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_PATTERN.findall(text)]


def _l2_normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return vector
    return [value / norm for value in vector]
