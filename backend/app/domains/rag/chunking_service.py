from app.domains.github.schema import GitHubFileSnapshotDTO
from app.domains.rag.chunker_registry import DEFAULT_CHUNKER_REGISTRY, ChunkerRegistry
from app.domains.rag.chunk_factory import DEFAULT_CHUNK_FACTORY, ChunkFactory
from app.domains.rag.snapshot_validator import (
    DEFAULT_SNAPSHOT_VALIDATOR,
    SnapshotValidator,
)
from app.domains.rag.schema import RagEvidenceChunkDTO


class ChunkingService:
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
