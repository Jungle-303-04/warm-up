# 애플리케이션 전역 의존성 주입 컨테이너를 정의하는 파일
# service, chunker, factory 같은 객체 생성과 연결 방식을 한 곳에서 관리
from pathlib import Path

from dependency_injector import containers, providers
from dotenv import load_dotenv

from app.domains.auth.application.auth_service import AuthService
from app.domains.auth.domain.jwt_service import JwtService
from app.domains.auth.infrastructure.github_oauth_client import GitHubOAuthClient
from app.domains.auth.infrastructure.sql_repository import AuthSqlRepository
from app.domains.github.application.github_service import GitHubService
from app.domains.github.domain.content_decoder import GitHubContentDecoder
from app.domains.github.domain.file_citation import GitHubFileCitationBuilder
from app.domains.github.domain.file_snapshot_builder import GitHubFileSnapshotBuilder
from app.domains.github.domain.language_detector import GitHubLanguageDetector
from app.domains.rag.application.index_service import RagIndexService
from app.domains.rag.application.pipeline import GitHubRagPipelineService
from app.domains.rag.domain.chunk_citation import ChunkCitationService
from app.domains.rag.domain.chunk_factory import ChunkFactory
from app.domains.rag.domain.chunk_identity import ChunkIdentityService
from app.domains.rag.domain.chunker_registry import ChunkerRegistry
from app.domains.rag.domain.chunking_base import TextSplitter
from app.domains.rag.domain.chunking_service import ChunkingService
from app.domains.rag.domain.markdown_chunker import MarkdownChunker
from app.domains.rag.domain.python_chunker import PythonChunker
from app.domains.rag.domain.python_classifier import PythonChunkClassifier
from app.domains.rag.domain.snapshot_validator import SnapshotValidator
from app.domains.rag.infrastructure.embedding import OpenAIEmbeddingService
from app.domains.rag.infrastructure.sql_repository import RagSqlRepository
from app.domains.rag.infrastructure.vector_repository import RagVectorRepository


ROOT_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ROOT_ENV_PATH)


# dependency injection container
class AppContainer(containers.DeclarativeContainer):
    # Auth domain providers
    auth_github_oauth_client = providers.Singleton(GitHubOAuthClient)
    auth_jwt_service = providers.Singleton(JwtService)
    auth_repository = providers.Singleton(AuthSqlRepository)
    auth_service = providers.Singleton(
        AuthService,
        github_oauth_client=auth_github_oauth_client,
        jwt_service=auth_jwt_service,
        auth_repository=auth_repository,
    )

    # GitHub domain providers
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

    # RAG chunker providers
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

    # RAG chunk creation providers
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

    # RAG pipeline provider
    rag_pipeline_service = providers.Singleton(
        GitHubRagPipelineService,
        snapshot_builder=github_file_snapshot_builder,
        chunking_service=chunking_service,
    )
    rag_sql_repository = providers.Singleton(RagSqlRepository)
    rag_embedding_service = providers.Singleton(OpenAIEmbeddingService)
    rag_vector_repository = providers.Singleton(
        RagVectorRepository,
        embedding_service=rag_embedding_service,
    )
    rag_index_service = providers.Singleton(
        RagIndexService,
        pipeline_service=rag_pipeline_service,
        sql_repository=rag_sql_repository,
        vector_repository=rag_vector_repository,
    )


# app에서 import해서 사용하는 container instance
container = AppContainer()
