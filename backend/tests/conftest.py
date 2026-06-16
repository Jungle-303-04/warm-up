"""테스트 공용 설정.

보호된 엔드포인트는 get_current_claims(세션 인증)에 의존한다. 테스트에서는
실제 OAuth 세션을 만들 수 없으므로, 공유 app 인스턴스의 해당 의존성을
더미 사용자로 오버라이드한다.

- /auth/me, github 웹훅 등은 get_current_claims를 쓰지 않으므로(쿠키/서명 직접 검증)
  이 오버라이드의 영향을 받지 않는다(401 기대 테스트 유지).
- 모듈 수준 TestClient(app)도 같은 app 객체를 공유하므로 요청 시점에 적용된다.
"""

import pytest

from app.auth.dependencies import get_current_claims
from app.auth.domain.records import SessionClaims
from app.main import app


@pytest.fixture(autouse=True)
def _override_auth():
    app.dependency_overrides[get_current_claims] = lambda: SessionClaims(user_id=1, login="test")
    yield
    app.dependency_overrides.pop(get_current_claims, None)
