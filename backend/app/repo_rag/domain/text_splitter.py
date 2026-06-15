"""재귀 문자 분할기.

langchain-text-splitters가 설치돼 있으면 그것을 쓰고, 없으면 동일한 동작의
의존성 없는 폴백 구현을 사용한다. 둘 다 같은 `split(text)` 인터페이스를 제공한다.
"""

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 120
TEXT_SPLIT_SEPARATORS = ["\n\n", "\n", " ", ""]


class _FallbackRecursiveSplitter:
    def __init__(self, chunk_size: int, chunk_overlap: int, separators: list[str]) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators

    def split_text(self, text: str) -> list[str]:
        chunks = self._split(text, self.separators)
        return [chunk for chunk in chunks if chunk.strip()]

    def _split(self, text: str, separators: list[str]) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]

        if not separators:
            return self._split_by_size(text)

        separator, *rest = separators
        if separator == "":
            return self._split_by_size(text)

        chunks: list[str] = []
        buffer = ""

        for part in text.split(separator):
            candidate = part if not buffer else f"{buffer}{separator}{part}"
            if len(candidate) <= self.chunk_size:
                buffer = candidate
                continue

            if buffer:
                chunks.append(buffer)
                buffer = ""

            if len(part) > self.chunk_size:
                chunks.extend(self._split(part, rest))
            else:
                buffer = part

        if buffer:
            chunks.append(buffer)

        return chunks

    def _split_by_size(self, text: str) -> list[str]:
        step = max(1, self.chunk_size - self.chunk_overlap)
        return [text[start : start + self.chunk_size] for start in range(0, len(text), step)]


class TextSplitterService:
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        separators: list[str] | None = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or list(TEXT_SPLIT_SEPARATORS)
        self._splitter = self._build_splitter()

    def _build_splitter(self) -> object:
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter  # type: ignore
        except ImportError:
            return _FallbackRecursiveSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=self.separators,
            )

        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=self.separators,
        )

    def split(self, text: str) -> list[str]:
        return [chunk for chunk in self._splitter.split_text(text) if chunk.strip()]  # type: ignore


DEFAULT_TEXT_SPLITTER_SERVICE = TextSplitterService()
