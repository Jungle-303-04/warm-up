from app.pipeline.api.schemas import CodeReference, RepoSnapshot
from app.pipeline.domain.symbol_extractor import (
    PythonSymbolExtractor,
    Symbol,
    SymbolExtractor,
)


VERIFIED = "verified"
DEFAULT_EXTRACTORS: tuple[SymbolExtractor, ...] = (PythonSymbolExtractor(),)


class CodeIndexService:
    def __init__(
        self, extractors: tuple[SymbolExtractor, ...] = DEFAULT_EXTRACTORS
    ) -> None:
        self._extractors = extractors

    def index(self, snapshot: RepoSnapshot) -> list[CodeReference]:
        references: list[CodeReference] = []

        for file in snapshot.files:
            symbols = self._extract_symbols(file.path, file.content)

            if not symbols:
                references.append(
                    CodeReference(
                        id=f"{file.path}:file",
                        path=file.path,
                        symbol="file",
                        kind="file",
                        line=1,
                        commit_sha=snapshot.commit_sha,
                        status=VERIFIED,
                    )
                )
                continue

            for symbol in symbols:
                references.append(
                    CodeReference(
                        id=f"{file.path}:{symbol.name}",
                        path=file.path,
                        symbol=symbol.name,
                        kind=symbol.kind,
                        line=symbol.line,
                        commit_sha=snapshot.commit_sha,
                        status=VERIFIED,
                    )
                )

        return references

    def _extract_symbols(self, path: str, content: str) -> list[Symbol]:
        for extractor in self._extractors:
            if extractor.supports(path):
                return extractor.extract(content)
        return []
