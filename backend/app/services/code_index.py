from app.schemas.pipeline import CodeReference, RepoSnapshot


class CodeIndexService:
    def index(self, snapshot: RepoSnapshot) -> list[CodeReference]:
        # tree-sitter 같은 parser를 붙이기 전까지는 간단한 함수 선언만 symbol로 본다.
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
        # 최소 구현용 naive parser다. 이후 언어별 parser로 교체할 자리다.
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
