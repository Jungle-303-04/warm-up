"""GitHub OAuth 로그인 유스케이스.

start_login: state 발급 + authorize URL 생성(사용자를 GitHub로 보냄).
complete_login: state 검증 → code를 access token으로 교환 → 사용자 조회 →
                토큰 저장 → 서비스 세션 JWT 발급.
current_user: 세션 JWT 검증.
"""

from dataclasses import dataclass

from app.auth.domain.oauth import build_authorize_url, generate_state, verify_state
from app.auth.domain.ports import GitHubOAuthClient, GitHubTokenStore
from app.auth.domain.records import GitHubUser, SessionClaims
from app.auth.infrastructure.session_tokens import SessionTokenCodec


@dataclass(frozen=True, slots=True)
class LoginResult:
    session_token: str
    user: GitHubUser


@dataclass(slots=True)
class AuthService:
    oauth_client: GitHubOAuthClient
    token_store: GitHubTokenStore
    session_codec: SessionTokenCodec
    client_id: str
    redirect_uri: str
    scope: str

    def start_login(self) -> tuple[str, str]:
        state = generate_state()
        url = build_authorize_url(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
            state=state,
        )
        return url, state

    def complete_login(
        self,
        code: str,
        received_state: str | None,
        expected_state: str | None,
    ) -> LoginResult:
        if not expected_state or not verify_state(expected_state, received_state):
            raise ValueError("state 검증에 실패했습니다(잘못된 로그인 요청)")

        access_token = self.oauth_client.exchange_code(code)
        user = self.oauth_client.fetch_user(access_token)
        self.token_store.save(user.id, access_token)
        session_token = self.session_codec.issue(user.id, user.login)
        return LoginResult(session_token=session_token, user=user)

    def current_user(self, session_token: str) -> SessionClaims:
        return self.session_codec.verify(session_token)
