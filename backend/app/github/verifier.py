import logging
from typing import Protocol
from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class GitHubAppConfigVerifier(Protocol):
    """GitHub App 및 OAuth 설정의 검증 책임을 가지는 포트."""

    def verify(self) -> bool:
        """설정을 검증하고 적절히 구성되어 있으면 True를 반환합니다."""
        ...


class RealGitHubAppConfigVerifier:
    """실제 GitHub App 설정값들의 정합성을 체크하는 검증기."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def verify(self) -> bool:
        client_id = self._settings.github_oauth_client_id
        client_secret = self._settings.github_oauth_client_secret

        if not client_id or not client_secret:
            logger.warning("GitHub OAuth 설정 누락: GITHUB_OAUTH_CLIENT_ID 또는 CLIENT_SECRET 미설정")
            return False

        logger.info("GitHub App 및 OAuth 설정 확인 완료")
        return True


class MockGitHubAppConfigVerifier:
    """로컬 및 테스트 환경을 위한 모의 검증기 (설정이 비어있어도 mock 모드로 통과)."""

    def verify(self) -> bool:
        logger.info("GitHub App 설정을 모의 모드(Mock Mode)로 통과시킵니다.")
        return True
