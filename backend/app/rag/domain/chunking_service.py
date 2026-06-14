from app.github.api.schema import GitHubFileSnapshotDTO
from app.rag.api.schema import RagEvidenceChunkDTO
from app.rag.domain.chunk_factory import DEFAULT_CHUNK_FACTORY, ChunkFactory
from app.rag.domain.chunker_registry import DEFAULT_CHUNKER_REGISTRY, ChunkerRegistry
from app.rag.domain.snapshot_validator import (
    DEFAULT_SNAPSHOT_VALIDATOR,
    SnapshotValidator,
)


class ChunkingService:
    """파일 검증, 언어별 청킹, 최종 evidence DTO 생성을 한 흐름으로 묶는다."""

    def __init__(
        self,
        chunkers: ChunkerRegistry,
        factory: ChunkFactory,
        validator: SnapshotValidator,
    ) -> None:
        self.chunkers = chunkers
        self.factory = factory
        self.validator = validator

    def build_minimal_evidence_chunks(
        self,
        file_snapshot: GitHubFileSnapshotDTO,
    ) -> list[RagEvidenceChunkDTO]:
        """지원 언어만 청크로 만들고, Python/Markdown 외 파일은 조용히 건너뛴다."""

        self.validator.validate(file_snapshot)

        chunker = self.chunkers.get(file_snapshot.language)
        if chunker is None:
            return []

        draft_chunks = chunker.build_chunks(file_snapshot)
        return self.factory.build_many(file_snapshot, draft_chunks)


DEFAULT_CHUNKING_SERVICE = ChunkingService(
    chunkers=DEFAULT_CHUNKER_REGISTRY,
    factory=DEFAULT_CHUNK_FACTORY,
    validator=DEFAULT_SNAPSHOT_VALIDATOR,
)
