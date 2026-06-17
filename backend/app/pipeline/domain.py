"""RAG 분석 파이프라인 단계 및 심볼 분석 비즈니스 규칙 정의."""

import ast
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import NamedTuple, Any

from app.pipeline.router import (
    AgentProposal,
    CodeReference,
    ProposalStatus,
    ProposalType,
    RepoSnapshot,
    RetrievalChunk,
    StageResult,
)


# --- 1. 파이프라인 단계 정의 (stages.py) ---
REPO_SYNC = "repo-sync"
CODE_INDEX = "code-index"
RAG_INDEX = "rag-index"
AGENT_PROPOSAL = "agent-proposal"
APPROVAL = "approval"

DONE = "done"


@dataclass(frozen=True)
class PipelineStage:
    id: str
    name: str
    purpose: str


ALL: tuple[PipelineStage, ...] = (
    PipelineStage(
        id=REPO_SYNC,
        name="저장소 동기화",
        purpose="요청 파일 또는 원격 Git 저장소를 읽어 저장소 스냅샷을 만든다.",
    ),
    PipelineStage(
        id=CODE_INDEX,
        name="코드 인덱싱",
        purpose="스냅샷 파일에서 함수와 파일 단위 참조 정보를 추출한다.",
    ),
    PipelineStage(
        id=RAG_INDEX,
        name="RAG 인덱싱",
        purpose="참조된 파일 내용을 검색과 근거 제시에 사용할 텍스트 조각으로 만든다.",
    ),
    PipelineStage(
        id=AGENT_PROPOSAL,
        name="에이전트 제안",
        purpose="코드 참조와 검색 조각을 근거로 사용자가 검토할 제안을 만든다.",
    ),
    PipelineStage(
        id=APPROVAL,
        name="승인 처리",
        purpose="생성된 제안을 승인 상태로 바꾸어 다음 단계에서 사용할 수 있게 한다.",
    ),
)

IDS: tuple[str, ...] = tuple(stage.id for stage in ALL)
WORKER_IDS: tuple[str, ...] = tuple(
    stage.id for stage in ALL if stage.id != APPROVAL
)


def build_done_stage_results(details: Mapping[str, str]) -> list[StageResult]:
    return [
        StageResult(id=stage_id, status=DONE, detail=details[stage_id])
        for stage_id in IDS
    ]


# --- 2. 심볼 추출기 정의 (symbol_extractor.py) ---
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


# --- 3. 코드 인덱싱 서비스 정의 (code_index.py) ---
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


# --- 4. RAG 인덱싱 서비스 정의 (rag_index.py) ---
class RagIndexService:
    def index(
        self,
        snapshot: RepoSnapshot,
        references: list[CodeReference],
    ) -> list[RetrievalChunk]:
        reference_paths = {reference.path for reference in references}
        chunks: list[RetrievalChunk] = []

        for file in snapshot.files:
            if file.path not in reference_paths:
                continue

            text = file.content.strip()
            if not text:
                continue

            chunks.append(
                RetrievalChunk(
                    id=f"{file.path}@{snapshot.commit_sha}",
                    source_path=file.path,
                    text=text[:800],
                    citation=f"{snapshot.repository}:{file.path}@{snapshot.commit_sha}",
                )
            )

        return chunks


# --- 5. 제안 승인 서비스 정의 (approval.py) ---
class ApprovalService:
    def approve(self, proposals: list[AgentProposal]) -> list[AgentProposal]:
        return [
            proposal.model_copy(update={"status": ProposalStatus.APPROVED})
            for proposal in proposals
        ]


# --- 6. 제안 생성 서비스 정의 (agent.py) ---
WITH_EVIDENCE = 0.7
WITHOUT_EVIDENCE = 0.4
CHANGE_TEMPLATE = "문서 컨텍스트를 {path}:{symbol} 코드와 연결하세요."


# LlmProposer는 상호 참조 오류 방지를 위해 동적으로 proposer.py에서 import함
@dataclass(slots=True)
class AgentProposalService:
    """제안 생성 유스케이스.

    proposer(LLM 포트)가 주입되면 그 초안으로 제안을 만들고,
    없으면 증거 기반 휴리스틱으로 동작한다(오프라인/테스트 기본값).
    """

    proposer: Any = None

    def propose(
        self,
        references: list[CodeReference],
        chunks: list[RetrievalChunk],
    ) -> list[AgentProposal]:
        if not references:
            return []

        if self.proposer is not None:
            drafts = self.proposer.generate(references, chunks)
            return [self._to_proposal(index, draft) for index, draft in enumerate(drafts)]

        return self._heuristic(references, chunks)

    def _to_proposal(self, index: int, draft: Any) -> AgentProposal:
        return AgentProposal(
            id=f"proposal:{draft.target_path}:{index}",
            type=draft.type,
            status=ProposalStatus.PENDING,
            target_path=draft.target_path,
            evidence=draft.evidence,
            confidence=max(0.0, min(1.0, draft.confidence)),
            proposed_change=draft.proposed_change,
        )

    def _heuristic(
        self,
        references: list[CodeReference],
        chunks: list[RetrievalChunk],
    ) -> list[AgentProposal]:
        reference = references[0]
        evidence = [chunk.citation for chunk in chunks if chunk.source_path == reference.path]

        return [
            AgentProposal(
                id=f"proposal:{reference.id}",
                type=ProposalType.RELATED_CODE,
                status=ProposalStatus.PENDING,
                target_path=reference.path,
                evidence=evidence,
                confidence=WITH_EVIDENCE if evidence else WITHOUT_EVIDENCE,
                proposed_change=CHANGE_TEMPLATE.format(
                    path=reference.path,
                    symbol=reference.symbol,
                ),
            )
        ]
