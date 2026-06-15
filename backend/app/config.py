from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경변수 기반 애플리케이션 설정.

    POSTGRES_DATABASE_URL이 지정되면 repo-rag가 Postgres 저장소를 사용하고,
    없으면 in-memory 저장소로 동작한다.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_database_url: str | None = None

    # 임베딩
    embedding_provider: str = "deterministic"  # "deterministic" | "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    openai_api_key: str | None = None

    # LLM 제안 (에이전트). "none"이면 휴리스틱 fallback으로 동작한다.
    llm_provider: str = "none"  # "none" | "openai"
    llm_model: str = "gpt-4o-mini"

    # GitHub App
    github_app_id: str | None = None
    github_webhook_secret: str | None = None
    github_private_key_path: str | None = None

    # GitHub OAuth (사용자 로그인)
    github_oauth_client_id: str | None = None
    github_oauth_client_secret: str | None = None
    github_oauth_redirect_uri: str = "http://localhost:8000/auth/github/callback"
    github_oauth_scopes: str = "read:user repo"
    session_jwt_secret: str = "dev-insecure-session-secret"  # 운영에서는 반드시 교체
    session_ttl_seconds: int = 60 * 60 * 8
    web_app_url: str = "http://localhost:3000"  # 로그인 완료 후 돌아갈 프론트엔드

    # 하이브리드 검색 가중치 (vector + keyword)
    hybrid_vector_weight: float = 0.7
    hybrid_keyword_weight: float = 0.3

    # Postgres 전문검색 설정
    search_text_config: str = "simple"
    search_candidate_limit: int = 50

    @property
    def uses_postgres(self) -> bool:
        return bool(self.postgres_database_url)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
