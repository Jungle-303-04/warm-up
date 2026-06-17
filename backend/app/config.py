from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경변수 기반 애플리케이션 설정.

    POSTGRES_DATABASE_URL이 지정되면 repo-rag가 Postgres 저장소를 사용하고,
    없으면 in-memory 저장소로 동작한다.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_database_url: str | None = None
    repolm_env: str = "local"

    # 임베딩
    embedding_provider: str = "deterministic"  # "deterministic" | "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    openai_api_key: str | None = None

    # LLM 제안 (에이전트). 기본 openai — OPENAI_API_KEY가 있으면 UML/ERD/변경요약을
    # LLM으로 생성하고, 키가 없으면 자동으로 결정론(휴리스틱) 폴백으로 동작한다.
    llm_provider: str = "openai"  # "none" | "openai"
    llm_model: str = "gpt-4o-mini"

    # GitHub 웹훅
    github_webhook_secret: str | None = None

    # GitHub OAuth (사용자 로그인)
    github_oauth_client_id: str | None = None
    github_oauth_client_secret: str | None = None
    github_oauth_redirect_uri: str = "http://localhost:8000/auth/github/callback"
    github_oauth_scopes: str = "read:user repo"
    session_jwt_secret: str = "dev-insecure-session-secret"  # 운영에서는 반드시 교체
    session_ttl_seconds: int = 60 * 60 * 8
    web_app_url: str = "http://localhost:3000"  # 로그인 완료 후 돌아갈 프론트엔드
    cors_extra_origins: str = ""  # 쉼표 구분 추가 허용 origin(Vercel preview 등)

    # 하이브리드 검색 가중치 (vector + keyword)
    hybrid_vector_weight: float = 0.7
    hybrid_keyword_weight: float = 0.3

    # Postgres 전문검색 설정
    search_text_config: str = "simple"
    search_candidate_limit: int = 50

    # 산출물(UML/ERD/의존성/변경요약) 컨텍스트 수집 한도. .env로 환경별 오버라이드 가능.
    # 예: ARTIFACT_MAX_FILE_CHARS=8000. 키우면 정확도↑·LLM 비용/지연↑.
    artifact_max_file_chars: int = 4000  # 파일당 본문 상한
    artifact_max_total_context_chars: int = 20000  # 전체 컨텍스트 토큰 예산
    artifact_max_selected_files: int = 60  # 비-dependency 선별 파일 수 상한
    artifact_max_dependency_files: int = 250  # dependency 그래프용 .py 상한

    # 채팅 RAG 검색 top_k(.env로 오버라이드 가능). 의도별 검색 계획에서 상한으로 쓰인다.
    chat_default_top_k: int = 5  # 일반/코드/버그 질문 기본 top_k
    chat_architecture_top_k: int = 8  # 아키텍처 질문은 더 넓게 검색
    # 채팅 답변기가 인프로세스 도구(노트북 소스 파일 읽기·인덱스 코드 검색·심볼 찾기)를
    # 사용하는 에이전트 루프로 동작할지. 켜면 우리가 인덱싱한 레포를 라이브로 확인해 답함.
    chat_use_tools: bool = True
    chat_tool_max_steps: int = 4  # 에이전트 도구 호출 반복 상한(무한루프 방지)

    @property
    def uses_postgres(self) -> bool:
        return bool(self.postgres_database_url)

    @property
    def is_production(self) -> bool:
        return self.repolm_env.lower() in {"prod", "production"}

    @property
    def secure_cookies(self) -> bool:
        return self.is_production or self.web_app_url.startswith("https://")

    @property
    def session_cookie_samesite(self) -> Literal["lax", "none"]:
        # Vercel(frontend) -> public API tunnel/backend처럼 프론트와 API가 서로 다른
        # 사이트인 배포에서는 브라우저가 Lax 쿠키를 fetch credentials에 싣지 않는다.
        # HTTPS에서만 SameSite=None을 쓸 수 있으므로 로컬 HTTP 개발은 Lax를 유지한다.
        return "none" if self.secure_cookies and self.web_app_url.startswith("https://") else "lax"

    @property
    def allowed_web_origins(self) -> set[str]:
        origins = {
            self.web_app_url,
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        }
        origins.update(
            origin.strip()
            for origin in self.cors_extra_origins.split(",")
            if origin.strip()
        )
        return origins


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
