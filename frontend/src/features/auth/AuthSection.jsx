import { useState } from 'react'

export function AuthSection({
  user,
  status,
  isLoading,
  onLogin,
  onLogout,
  onHome,
  onStartCreateBoard,
  onOpenBoardSearch,
  onOpenRepositoryAnalysis,
  onOpenRepositoryRuns,
  theme,
  onToggleTheme,
  children,
}) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  if (user) {
    return (
      <>
        <aside
          className={`app-sidebar ${isSidebarOpen ? 'expanded' : ''}`}
          aria-label="앱 네비게이션"
        >
          <button
            type="button"
            className="sidebar-toggle"
            onClick={() => setIsSidebarOpen((current) => !current)}
            aria-label={isSidebarOpen ? '사이드바 접기' : '사이드바 펼치기'}
            aria-expanded={isSidebarOpen}
          >
            {isSidebarOpen ? <IconCollapse /> : <IconMenu />}
          </button>

          <nav className="sidebar-nav" aria-label="주요 화면">
            <button type="button" onClick={onHome}>
              <IconHome />
              <span>홈</span>
            </button>

            <section className="sidebar-section" aria-label="게시글">
              <h2>게시글</h2>
              <button type="button" onClick={onStartCreateBoard}>
                <IconWrite />
                <span>게시글 작성하기</span>
              </button>
              <button type="button" onClick={onOpenBoardSearch}>
                <IconBoard />
                <span>게시글 전체보기</span>
              </button>
            </section>

            <section className="sidebar-section" aria-label="레포지토리">
              <h2>레포지토리</h2>
              <button type="button" onClick={onOpenRepositoryAnalysis}>
                <IconRepository />
                <span>레포지토리 등록</span>
              </button>
              <button type="button" onClick={onOpenRepositoryRuns}>
                <IconRepositoryList />
                <span>등록된 레포지토리</span>
              </button>
            </section>

            <section className="sidebar-section" aria-label="설정">
              <h2>설정</h2>
              <button
                type="button"
                onClick={onToggleTheme}
                aria-label={theme === 'dark' ? '라이트 모드로 변경' : '다크 모드로 변경'}
              >
                {theme === 'dark' ? <IconSun /> : <IconMoon />}
                <span>{theme === 'dark' ? '라이트 모드' : '다크 모드'}</span>
              </button>
            </section>
          </nav>
        </aside>

        <div className="app-content">
          <header className="app-header">
            <button type="button" className="brand-row brand-button" onClick={onHome}>
              <span className="brand-mark" aria-hidden="true">
                <svg>
                  <use href="/icons.svg#github-icon" />
                </svg>
              </span>
              <span>Code-Trust Kanban</span>
            </button>

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

          <main className="dashboard-main">{children}</main>
        </div>
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
    </main>
  )
}

function IconMenu() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 6.5h16M4 12h16M4 17.5h16" />
    </svg>
  )
}

function IconCollapse() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="m15 6-6 6 6 6" />
    </svg>
  )
}

function IconWrite() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 19h4l10-10-4-4L5 15z" />
      <path d="m14 6 4 4" />
      <path d="M5 21h14" />
    </svg>
  )
}

function IconHome() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="m4 11 8-7 8 7" />
      <path d="M6.5 10.5V20h11v-9.5" />
      <path d="M10 20v-5h4v5" />
    </svg>
  )
}

function IconBoard() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M7 5h10" />
      <path d="M6 9h12" />
      <path d="M7 13h7" />
      <path d="M7 17h5" />
      <rect x="4" y="3.5" width="16" height="17" rx="2" />
    </svg>
  )
}

function IconRepository() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M6 4.5h9l3 3v12H6z" />
      <path d="M15 4.5V8h3" />
      <path d="M8.5 12h7" />
      <path d="M8.5 15.5h5" />
    </svg>
  )
}

function IconRepositoryList() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 6h14" />
      <path d="M5 12h14" />
      <path d="M5 18h14" />
      <path d="M3 6h.01" />
      <path d="M3 12h.01" />
      <path d="M3 18h.01" />
    </svg>
  )
}

function IconMoon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M20 14.5A7.5 7.5 0 0 1 9.5 4 8.5 8.5 0 1 0 20 14.5z" />
    </svg>
  )
}

function IconSun() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2" />
      <path d="M12 20v2" />
      <path d="m4.93 4.93 1.41 1.41" />
      <path d="m17.66 17.66 1.41 1.41" />
      <path d="M2 12h2" />
      <path d="M20 12h2" />
      <path d="m6.34 17.66-1.41 1.41" />
      <path d="m19.07 4.93-1.41 1.41" />
    </svg>
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
