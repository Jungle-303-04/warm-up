import hashlib
import math
from typing import Protocol

from langchain_openai import OpenAIEmbeddings


DEFAULT_EMBEDDING_DIMENSION = 64
HASH_BLOCK_SIZE = 32
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"


class EmbeddingService(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        pass

    def embed_text(self, text: str) -> list[float]:
        pass


class OpenAIEmbeddingService:
    def __init__(self, model: str = OPENAI_EMBEDDING_MODEL) -> None:
        self.embedding_model = OpenAIEmbeddings(model=model)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self.embedding_model.embed_documents(texts)

    def embed_text(self, text: str) -> list[float]:
        return self.embedding_model.embed_query(text)


class HashEmbeddingService:
    def __init__(self, dimension: int = DEFAULT_EMBEDDING_DIMENSION) -> None:
        self.dimension = dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0 for _ in range(self.dimension)]

        for index in range(0, self.dimension, HASH_BLOCK_SIZE):
            digest = hashlib.sha256(f"{index}:{text}".encode("utf-8")).digest()
            for offset, byte in enumerate(digest):
                vector_index = index + offset
                if vector_index >= self.dimension:
                    break
                vector[vector_index] = (byte / 127.5) - 1.0

        return normalize_vector(vector)


def normalize_vector(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]
