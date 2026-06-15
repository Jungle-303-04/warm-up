import ast
from abc import ABC, abstractmethod
from typing import NamedTuple


class Symbol(NamedTuple):
    name: str
    kind: str
    line: int


class SymbolExtractor(ABC):
    """언어별 심볼 추출기의 공통 인터페이스."""

    @abstractmethod
    def supports(self, path: str) -> bool:
        """이 추출기가 해당 파일을 처리할 수 있는지."""

    @abstractmethod
    def extract(self, content: str) -> list[Symbol]:
        """파일 내용에서 심볼을 추출."""


class PythonSymbolExtractor(SymbolExtractor):
    EXTENSIONS = (".py", ".pyi")

    def supports(self, path: str) -> bool:
        return path.endswith(self.EXTENSIONS)

    def extract(self, content: str) -> list[Symbol]:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []

        symbols: list[Symbol] = []
        for node in tree.body:
            symbols.extend(PythonSymbolExtractor._symbols_from_node(node))

        symbols.sort(key=lambda symbol: symbol.line)
        return symbols

    @staticmethod
    def _symbols_from_node(node: ast.AST) -> list[Symbol]:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return [Symbol(node.name, "function", node.lineno)]

        if isinstance(node, ast.ClassDef):
            symbols = [Symbol(node.name, "class", node.lineno)]
            for member in node.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.append(
                        Symbol(f"{node.name}.{member.name}", "method", member.lineno)
                    )
            return symbols

        return []
