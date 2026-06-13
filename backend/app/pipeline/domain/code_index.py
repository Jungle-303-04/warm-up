from app.pipeline.api.schemas import CodeReference, RepoSnapshot


class CodeIndexService:
    def index(self, snapshot: RepoSnapshot) -> list[CodeReference]:
        references: list[CodeReference] = []

        for file in snapshot.files:
            symbols = self._extract_symbols(file.content)

            if not symbols:
                references.append(
                    CodeReference(
                        id=f"{file.path}:file",
                        path=file.path,
                        symbol="file",
                        line=1,
                        commit_sha=snapshot.commit_sha,
                        status="verified",
                    )
                )
                continue

            for symbol, line in symbols:
                references.append(
                    CodeReference(
                        id=f"{file.path}:{symbol}",
                        path=file.path,
                        symbol=symbol,
                        line=line,
                        commit_sha=snapshot.commit_sha,
                        status="verified",
                    )
                )

        return references

    def _extract_symbols(self, content: str) -> list[tuple[str, int]]:
        symbols: list[tuple[str, int]] = []

        for index, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("async def "):
                symbols.append((stripped.removeprefix("async def ").split("(")[0], index))
            elif stripped.startswith("def "):
                symbols.append((stripped.removeprefix("def ").split("(")[0], index))
            elif stripped.startswith("function "):
                symbols.append((stripped.removeprefix("function ").split("(")[0], index))
            elif stripped.startswith("export function "):
                symbols.append((stripped.removeprefix("export function ").split("(")[0], index))

        return symbols
