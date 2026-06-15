from pathlib import Path

from dependency_injector import containers, providers
from dotenv import load_dotenv

from app.agent.external.echo_responder import EchoAgentResponder
from app.agent.external.memory_store import InMemoryChatStore
from app.agent.service.chat_service import AgentChatService
from app.external.http import HttpClient, UserAgentFilter
from app.auth.service.auth_service import AuthService
from app.auth.domain.jwt_service import JwtService
from app.auth.external.github_oauth_client import (
    USER_AGENT,
    GitHubOAuthClient,
)
from app.auth.external.sql_repository import AuthSqlRepository
from app.board.service.board_service import BoardService
from app.board.external.repository import BoardSqlRepository
from app.github.service.github_service import GitHubService
from app.github.domain.content_decoder import GitHubContentDecoder
from app.github.domain.file_citation import GitHubFileCitationBuilder
from app.github.domain.file_snapshot_builder import GitHubFileSnapshotBuilder
from app.github.domain.language_detector import GitHubLanguageDetector
from app.github.external.repository import GitHubRepositoryClient
from app.rag.service.answer_graph import RagAnswerGraph
from app.rag.service.answer_service import RagAnswerService
from app.rag.service.index_service import RagIndexService
from app.rag.service.pipeline import GitHubRagPipelineService
from app.rag.domain.chunk_citation import ChunkCitationService
from app.rag.domain.chunk_factory import ChunkFactory
from app.rag.domain.chunk_identity import ChunkIdentityService
from app.rag.domain.chunker_registry import ChunkerRegistry
from app.rag.domain.chunking_base import TextSplitter
from app.rag.domain.chunking_service import ChunkingService
from app.rag.domain.markdown_chunker import MarkdownChunker
from app.rag.domain.python_chunker import PythonChunker
from app.rag.domain.python_classifier import PythonChunkClassifier
from app.rag.domain.snapshot_validator import SnapshotValidator
from app.rag.external.embedding import OpenAIEmbeddingService
from app.rag.external.llm_client import (
    EvidenceFormatter,
    OpenAIGenerator,
    PromptBuilder,
    RagLlm,
)
from app.rag.external.sql_repository import RagSqlRepository
from app.rag.external.vector_repository import RagVectorRepository


ROOT_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ROOT_ENV_PATH)


class AppContainer(containers.DeclarativeContainer):
    """서비스, 저장소, 외부 클라이언트를 한 곳에서 조립해 라우터에 주입한다."""

    agent_chat_store = providers.Singleton(InMemoryChatStore)
    agent_responder = providers.Singleton(EchoAgentResponder)
    agent_chat_service = providers.Singleton(
        AgentChatService,
        store=agent_chat_store,
        responder=agent_responder,
    )

    http_user_agent_filter = providers.Singleton(
        UserAgentFilter,
        user_agent=USER_AGENT,
    )
    http_client = providers.Singleton(
        HttpClient,
        filters=providers.List(http_user_agent_filter),
    )

    board_repository = providers.Singleton(BoardSqlRepository)
    board_service = providers.Singleton(
        BoardService,
        board_repository=board_repository,
    )

    auth_github_oauth_client = providers.Singleton(
        GitHubOAuthClient,
        http_client=http_client,
    )
    auth_jwt_service = providers.Singleton(JwtService)
    auth_repository = providers.Singleton(AuthSqlRepository)
    auth_service = providers.Singleton(
        AuthService,
        github_oauth_client=auth_github_oauth_client,
        jwt_service=auth_jwt_service,
        auth_repository=auth_repository,
    )

    github_content_decoder = providers.Singleton(GitHubContentDecoder)
    github_language_detector = providers.Singleton(GitHubLanguageDetector)
    github_file_citation_builder = providers.Singleton(GitHubFileCitationBuilder)
    github_file_snapshot_builder = providers.Singleton(
        GitHubFileSnapshotBuilder,
        content_decoder=github_content_decoder,
        language_detector=github_language_detector,
        citation_builder=github_file_citation_builder,
    )
    github_repository_client = providers.Singleton(
        GitHubRepositoryClient,
        http_client=http_client,
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
        repository_source=github_repository_client,
    )

    rag_evidence_formatter = providers.Singleton(EvidenceFormatter)
    rag_prompt_builder = providers.Singleton(
        PromptBuilder,
        evidence_formatter=rag_evidence_formatter,
    )
    rag_text_generator = providers.Singleton(OpenAIGenerator)
    rag_llm_client = providers.Singleton(
        RagLlm,
        prompt_builder=rag_prompt_builder,
        text_generator=rag_text_generator,
    )
    rag_answer_graph = providers.Singleton(
        RagAnswerGraph,
        vector_repository=rag_vector_repository,
        llm_client=rag_llm_client,
    )
    rag_answer_service = providers.Singleton(
        RagAnswerService,
        answer_graph=rag_answer_graph,
    )


container = AppContainer()
