import { API_BASE_URL } from '../../app/config'

export function AuthSection({
  user,
  status,
  oauthState,
  isLoading,
  onLogin,
  onLogout,
  children,
}) {
  if (user) {
    return (
      <>
        <header className="app-header">
          <div className="brand-row">
            <span className="brand-mark" aria-hidden="true">
              <svg>
                <use href="/icons.svg#github-icon" />
              </svg>
            </span>
            <span>Code-Trust Kanban</span>
          </div>

          <nav className="dashboard-nav" aria-label="주요 화면">
            <a href="#calendar-title">캘린더</a>
            <a href="#workspace-title">레포지토리 분석</a>
          </nav>

          <div className="dashboard-account">
            <UserProfile user={user} />
            <button
              type="button"
              className="secondary-button compact"
              onClick={onLogout}
              disabled={isLoading}
            >
              로그아웃
            </button>
          </div>
        </header>

        <aside className="dashboard-meta" aria-label="연결 상태">
          <div className={`status-box ${status.type}`} role="status">
            {status.message}
          </div>
          <ConnectionStatus user={user} oauthState={oauthState} />
        </aside>

        <main className="dashboard-main">{children}</main>
      </>
    )
  }

  return (
    <main className="login-panel login-main" aria-labelledby="login-title">
      <div className="brand-row">
        <span className="brand-mark" aria-hidden="true">
          <svg>
            <use href="/icons.svg#github-icon" />
          </svg>
        </span>
        <span>Code-Trust Kanban</span>
      </div>

      <div className="headline">
        <p className="eyebrow">깃허브 계정 연결</p>
        <h1 id="login-title">깃허브로 로그인하세요</h1>
        <p>
          레포지토리 코드와 보드 계획을 비교하려면 먼저 깃허브 권한이 필요합니다.
        </p>
      </div>

      <button
        type="button"
        className="github-login-button"
        onClick={onLogin}
        disabled={isLoading}
      >
        <svg aria-hidden="true">
          <use href="/icons.svg#github-icon" />
        </svg>
        {isLoading ? '로그인 준비 중' : '깃허브로 로그인'}
      </button>

      <div className={`status-box ${status.type}`} role="status">
        {status.message}
      </div>

      <ConnectionStatus user={user} oauthState={oauthState} />
    </main>
  )
}

function UserProfile({ user }) {
  return (
    <div className="profile-panel">
      {user.avatar_url ? (
        <img src={user.avatar_url} alt="" className="profile-avatar" />
      ) : (
        <span className="profile-avatar placeholder" aria-hidden="true" />
      )}
      <div>
        <strong>{user.login}</strong>
        <span>{user.email || '이메일 비공개'}</span>
      </div>
    </div>
  )
}

function ConnectionStatus({ user, oauthState }) {
  return (
    <dl className="connection-list">
      <div>
        <dt>API 주소</dt>
        <dd>{API_BASE_URL}</dd>
      </div>
      <div>
        <dt>로그인 상태</dt>
        <dd>{user ? '쿠키 세션 확인됨' : '로그인 필요'}</dd>
      </div>
      <div>
        <dt>OAuth 상태</dt>
        <dd>{oauthState ? '상태값 발급됨' : '대기 중'}</dd>
      </div>
    </dl>
  )
}
