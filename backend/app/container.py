from dependency_injector import containers, providers

from app.domains.github.service import (
    GitHubContentDecoder,
    GitHubFileCitationBuilder,
    GitHubFileSnapshotBuilder,
    GitHubLanguageDetector,
    GitHubService,
)
from app.domains.rag.chunk_citation import ChunkCitationService
from app.domains.rag.chunk_factory import ChunkFactory
from app.domains.rag.chunk_identity import ChunkIdentityService
from app.domains.rag.chunker_registry import ChunkerRegistry
from app.domains.rag.chunking_base import TextSplitter
from app.domains.rag.chunking_service import ChunkingService
from app.domains.rag.markdown_chunker import MarkdownChunker
from app.domains.rag.pipeline import GitHubRagPipelineService
from app.domains.rag.python_chunker import PythonChunker
from app.domains.rag.python_classifier import PythonChunkClassifier
from app.domains.rag.snapshot_validator import SnapshotValidator


class AppContainer(containers.DeclarativeContainer):
    github_content_decoder = providers.Singleton(GitHubContentDecoder)
    github_language_detector = providers.Singleton(GitHubLanguageDetector)
    github_file_citation_builder = providers.Singleton(GitHubFileCitationBuilder)
    github_file_snapshot_builder = providers.Singleton(
        GitHubFileSnapshotBuilder,
        content_decoder=github_content_decoder,
        language_detector=github_language_detector,
        citation_builder=github_file_citation_builder,
    )
    github_service = providers.Singleton(
        GitHubService,
        snapshot_builder=github_file_snapshot_builder,
    )

    text_splitter = providers.Singleton(TextSplitter)
    python_classifier = providers.Singleton(PythonChunkClassifier)
    python_chunker = providers.Singleton(
        PythonChunker,
        classifier=python_classifier,
        text_splitter=text_splitter,
    )
    markdown_chunker = providers.Singleton(MarkdownChunker)
    chunker_registry = providers.Singleton(
        ChunkerRegistry,
        chunkers=providers.List(
            python_chunker,
            markdown_chunker,
        ),
    )

    chunk_identity = providers.Singleton(ChunkIdentityService)
    chunk_citation = providers.Singleton(ChunkCitationService)
    chunk_factory = providers.Singleton(
        ChunkFactory,
        identity=chunk_identity,
        citation=chunk_citation,
    )
    snapshot_validator = providers.Singleton(SnapshotValidator)
    chunking_service = providers.Singleton(
        ChunkingService,
        chunkers=chunker_registry,
        factory=chunk_factory,
        validator=snapshot_validator,
    )
    rag_pipeline_service = providers.Singleton(
        GitHubRagPipelineService,
        snapshot_builder=github_file_snapshot_builder,
        chunking_service=chunking_service,
    )


container = AppContainer()
