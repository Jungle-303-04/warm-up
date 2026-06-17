from pathlib import Path

from dependency_injector import containers, providers
from dotenv import load_dotenv

from app.agent.external.memory_store import InMemoryChatStore
from app.agent.external.text_generator import OpenAITextGenerator
from app.agent.external.tool_calling_llm import LangChainToolCallingLlm
from app.agent.service.agent_graph import AgentGraph
from app.agent.service.chat_service import AgentChatService
from app.agent.service.graph_responder import GraphAgentResponder
from app.agent.service.intent_resolver import AgentIntentResolver
from app.agent.service.repository_planner import AgentRepositoryPlanner
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
from app.rag.external.sql_repository import RagSqlRepository
from app.rag.external.vector_repository import RagVectorRepository


ROOT_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ROOT_ENV_PATH)


class AppContainer(containers.DeclarativeContainer):
    """앱에서 쓰는 객체를 만들고 연결하는 조립 지점이다."""

    # Common: 외부 API 호출에 공통으로 들어가는 HTTP 부품이다.
    http_user_agent_filter = providers.Singleton(
        UserAgentFilter,
        user_agent=USER_AGENT,
    )
    http_client = providers.Singleton(
        HttpClient,
        filters=providers.List(http_user_agent_filter),
    )

    # Board: 보드 API가 사용할 저장소와 서비스만 조립한다.
    board_repository = providers.Singleton(BoardSqlRepository)
    board_service = providers.Singleton(
        BoardService,
        board_repository=board_repository,
    )

    # Auth: GitHub OAuth, JWT, 사용자 계정 저장소를 인증 서비스에 묶는다.
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

    # GitHub: GitHub API 응답을 코드 스냅샷으로 바꾸는 부품이다.
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

    # RAG chunking: 파일 스냅샷을 검색 가능한 evidence chunk로 나눈다.
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

    # RAG storage: SQL과 vector DB에 저장하고 검색하는 공통 저장소다.
    rag_sql_repository = providers.Singleton(RagSqlRepository)
    rag_embedding_service = providers.Singleton(OpenAIEmbeddingService)
    rag_vector_repository = providers.Singleton(
        RagVectorRepository,
        embedding_service=rag_embedding_service,
    )

    # RAG indexing: GitHub 파일을 chunk로 바꿔 SQL/vector DB에 저장한다.
    rag_pipeline_service = providers.Singleton(
        GitHubRagPipelineService,
        snapshot_builder=github_file_snapshot_builder,
        chunking_service=chunking_service,
    )
    rag_index_service = providers.Singleton(
        RagIndexService,
        pipeline_service=rag_pipeline_service,
        sql_repository=rag_sql_repository,
        vector_repository=rag_vector_repository,
        repository_source=github_repository_client,
    )

    # RAG ask: 저장된 evidence를 벡터 유사도 기반으로 찾는 검색 tool 역할만 맡는다.
    rag_answer_graph = providers.Singleton(
        RagAnswerGraph,
        vector_repository=rag_vector_repository,
    )
    rag_answer_service = providers.Singleton(
        RagAnswerService,
        answer_graph=rag_answer_graph,
        sql_repository=rag_sql_repository,
    )

    # Agent chat: graph가 먼저 질문 의도를 나누고, 코드 질문일 때만 RAG evidence와 LLM 답변 생성을 연결한다.
    # 기준 변경은 tool 호출이 아니라 AgentGraph의 change_repository_basis 노드에서 refs를 계산한다.
    # TODO(agent): MCP action, 사용자 승인 노드를 AgentGraph에 추가한다.
    agent_chat_store = providers.Singleton(InMemoryChatStore)
    agent_tool_calling_llm = providers.Singleton(LangChainToolCallingLlm)
    agent_text_generator = providers.Singleton(OpenAITextGenerator)
    agent_repository_planner = providers.Singleton(
        AgentRepositoryPlanner,
        text_generator=agent_text_generator,
    )
    agent_intent_resolver = providers.Singleton(
        AgentIntentResolver,
        text_generator=agent_text_generator,
    )
    agent_graph = providers.Singleton(
        AgentGraph,
        rag_answer_service=rag_answer_service,
        sql_repository=rag_sql_repository,
        tool_calling_llm=agent_tool_calling_llm,
        repository_planner=agent_repository_planner,
        intent_resolver=agent_intent_resolver,
    )
    agent_responder = providers.Singleton(
        GraphAgentResponder,
        agent_graph=agent_graph,
    )
    agent_chat_service = providers.Singleton(
        AgentChatService,
        store=agent_chat_store,
        responder=agent_responder,
    )


container = AppContainer()
