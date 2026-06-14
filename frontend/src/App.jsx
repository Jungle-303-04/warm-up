import { useEffect, useState } from 'react'
import './App.css'

const API_BASE_URL = normalizeApiBaseUrl(
  import.meta.env.VITE_API_BASE_URL || '/api',
)
const OAUTH_STATE_STORAGE_KEY = 'warm-up.auth.githubState'
const LEGACY_ACCESS_TOKEN_STORAGE_KEY = 'warm-up.auth.accessToken'
const CALLBACK_PATH = '/auth/callback'
const INITIAL_STATUS = {
  type: 'muted',
  message: '로그인 전입니다.',
}

function App() {
  const [status, setStatus] = useState(INITIAL_STATUS)
  const [oauthState, setOauthState] = useState(
    window.localStorage.getItem(OAUTH_STATE_STORAGE_KEY) || '',
  )
  const [user, setUser] = useState(null)
  const [repositoryFullName, setRepositoryFullName] = useState('')
  const [branch, setBranch] = useState('')
  const [indexResult, setIndexResult] = useState(null)
  const [question, setQuestion] = useState('')
  const [answerResult, setAnswerResult] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [activeAction, setActiveAction] = useState('')

  const isIndexing = activeAction === 'index'
  const isAsking = activeAction === 'ask'

  async function startGithubLogin() {
    setIsLoading(true)
    setActiveAction('login')
    setStatus({ type: 'muted', message: '깃허브 로그인 주소를 요청하는 중입니다.' })

    try {
      const payload = await fetchJson(`${API_BASE_URL}/auth/github/login`)
      setOauthState(payload.state)
      window.localStorage.setItem(OAUTH_STATE_STORAGE_KEY, payload.state)
      setStatus({ type: 'success', message: '깃허브 로그인 페이지로 이동합니다.' })
      window.location.assign(payload.authorize_url)
    } catch (error) {
      setStatus({ type: 'error', message: toKoreanErrorMessage(error.message) })
    } finally {
      setIsLoading(false)
      setActiveAction('')
    }
  }

  async function loadAuthenticatedUser(message, options = {}) {
    setIsLoading(true)
    setActiveAction('auth')
    setStatus({ type: 'muted', message })

    try {
      const payload = await fetchJson(`${API_BASE_URL}/auth/me`)
      setUser(payload.user)
      setStatus({ type: 'success', message: '깃허브 로그인이 완료되었습니다.' })
    } catch (error) {
      if (options.silentUnauthenticated) {
        setStatus(INITIAL_STATUS)
      } else {
        setStatus({ type: 'error', message: toKoreanErrorMessage(error.message) })
      }
      setUser(null)
    } finally {
      setIsLoading(false)
      setActiveAction('')
    }
  }

  async function logout() {
    setIsLoading(true)
    setActiveAction('logout')
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    }).catch(() => undefined)
    clearSession()
    setUser(null)
    setOauthState('')
    setIndexResult(null)
    setAnswerResult(null)
    setStatus({ type: 'muted', message: '로그아웃되었습니다.' })
    setIsLoading(false)
    setActiveAction('')
  }

  async function indexRepository(event) {
    event.preventDefault()
    const repositoryName = repositoryFullName.trim()
    if (!repositoryName.includes('/')) {
      setStatus({ type: 'error', message: '레포지토리는 owner/repo 형식으로 입력해 주세요.' })
      return
    }

    setIsLoading(true)
    setActiveAction('index')
    setAnswerResult(null)
    setStatus({ type: 'muted', message: '레포지토리를 분석하고 DB에 저장하는 중입니다.' })

    try {
      const payload = await postJson(
        `${API_BASE_URL}/rag/github/repository/index/store`,
        {
          repository_full_name: repositoryName,
          branch: branch.trim() || null,
        },
      )
      setIndexResult(payload)
      setStatus({
        type: 'success',
        message: `분석 완료: SQL ${payload.sql_chunk_count}개, Vector ${payload.vector_chunk_count}개 저장`,
      })
    } catch (error) {
      setStatus({ type: 'error', message: toKoreanErrorMessage(error.message) })
    } finally {
      setIsLoading(false)
      setActiveAction('')
    }
  }

  async function askRepository(event) {
    event.preventDefault()
    if (!indexResult?.run_id) {
      setStatus({ type: 'error', message: '먼저 레포지토리 분석을 실행해 주세요.' })
      return
    }

    setIsLoading(true)
    setActiveAction('ask')
    setStatus({ type: 'muted', message: '저장된 근거로 답변을 생성하는 중입니다.' })

    try {
      const payload = await postJson(`${API_BASE_URL}/rag/ask`, {
        question,
        run_id: indexResult.run_id,
        limit: 5,
      })
      setAnswerResult(payload)
      setStatus({ type: 'success', message: 'LLM 액션이 완료되었습니다.' })
    } catch (error) {
      setStatus({ type: 'error', message: toKoreanErrorMessage(error.message) })
    } finally {
      setIsLoading(false)
      setActiveAction('')
    }
  }

  useEffect(() => {
    const timerId = window.setTimeout(() => {
      window.localStorage.removeItem(LEGACY_ACCESS_TOKEN_STORAGE_KEY)

      if (isGithubCallbackPage()) {
        clearCallbackUrl()
        void loadAuthenticatedUser('깃허브 로그인을 완료하는 중입니다.')
        return
      }

      void loadAuthenticatedUser('기존 로그인 상태를 확인하는 중입니다.', {
        silentUnauthenticated: true,
      })
    }, 0)

    return () => window.clearTimeout(timerId)
  }, [])

  return (
    <main className="auth-shell">
      <section className="login-panel" aria-labelledby="login-title">
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
          <h1 id="login-title">
            {user ? '로그인 완료' : '깃허브로 로그인하세요'}
          </h1>
          <p>
            {user
              ? '이제 연결된 깃허브 권한으로 레포지토리 분석을 시작할 수 있습니다.'
              : '레포지토리 코드와 보드 계획을 비교하려면 먼저 깃허브 권한이 필요합니다.'}
          </p>
        </div>

        {user ? (
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
        ) : (
          <button
            type="button"
            className="github-login-button"
            onClick={startGithubLogin}
            disabled={isLoading}
          >
            <svg aria-hidden="true">
              <use href="/icons.svg#github-icon" />
            </svg>
            {isLoading ? '로그인 준비 중' : '깃허브로 로그인'}
          </button>
        )}

        <div className={`status-box ${status.type}`} role="status">
          {status.message}
        </div>

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

        {user ? (
          <button
            type="button"
            className="secondary-button"
            onClick={logout}
            disabled={isLoading}
          >
            로그아웃
          </button>
        ) : null}

        {user ? (
          <section className="workspace-panel" aria-labelledby="workspace-title">
            <h2 id="workspace-title">레포지토리 분석</h2>

            <form className="workspace-form" onSubmit={indexRepository}>
              <label>
                <span>레포지토리</span>
                <input
                  type="text"
                  value={repositoryFullName}
                  onChange={(event) => setRepositoryFullName(event.target.value)}
                  placeholder="owner/repo 또는 GitHub URL"
                  autoComplete="off"
                  disabled={isLoading}
                />
              </label>

              <label>
                <span>브랜치</span>
                <input
                  type="text"
                  value={branch}
                  onChange={(event) => setBranch(event.target.value)}
                  placeholder="비워두면 기본 브랜치 전체 분석"
                  autoComplete="off"
                  disabled={isLoading}
                />
              </label>

              <button type="submit" className="primary-action" disabled={isLoading}>
                {isIndexing ? '분석 중' : '분석 시작'}
              </button>

              {isIndexing ? (
                <div className="progress-panel" role="status" aria-live="polite">
                  <div className="progress-header">
                    <span>레포지토리 전체 파일을 검사하고 있습니다.</span>
                    <strong>진행 중</strong>
                  </div>
                  <div className="progress-track" role="progressbar">
                    <span />
                  </div>
                </div>
              ) : null}
            </form>

            {indexResult ? (
              <dl className="run-summary">
                <div>
                  <dt>Run</dt>
                  <dd>{indexResult.run_id}</dd>
                </div>
                <div>
                  <dt>SQL</dt>
                  <dd>{indexResult.sql_chunk_count}</dd>
                </div>
                <div>
                  <dt>Vector</dt>
                  <dd>{indexResult.vector_chunk_count}</dd>
                </div>
              </dl>
            ) : null}

            <form className="workspace-form" onSubmit={askRepository}>
              <label>
                <span>질문</span>
                <textarea
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  placeholder="이 레포 기준으로 다음 구현 계획을 제안해줘"
                  rows="4"
                  disabled={isLoading}
                />
              </label>

              <button
                type="submit"
                className="primary-action"
                disabled={isLoading || !indexResult}
              >
                {isAsking ? '답변 생성 중' : 'LLM 액션 실행'}
              </button>

              {isAsking ? (
                <div className="progress-panel" role="status" aria-live="polite">
                  <div className="progress-header">
                    <span>저장된 RAG 근거를 찾고 LLM 답변을 생성하고 있습니다.</span>
                    <strong>진행 중</strong>
                  </div>
                  <div className="progress-track" role="progressbar">
                    <span />
                  </div>
                </div>
              ) : null}
            </form>

            {answerResult ? (
              <section className="answer-panel" aria-label="LLM 답변">
                <p>{answerResult.answer}</p>
                <ul>
                  {answerResult.sources.map((source) => (
                    <li key={`${source.citation}-${source.distance}`}>
                      {source.citation}
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}
          </section>
        ) : null}
      </section>
    </main>
  )
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(options.headers || {}),
    },
  })
  const payload = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(resolveErrorMessage(payload, response.status))
  }

  return payload
}

async function postJson(url, body) {
  return fetchJson(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
}

function normalizeApiBaseUrl(value) {
  return value.replace(/\/$/, '')
}

function resolveErrorMessage(payload, status) {
  if (payload?.detail) {
    return typeof payload.detail === 'string'
      ? payload.detail
      : JSON.stringify(payload.detail)
  }

  return `요청 실패: ${status}`
}

function toKoreanErrorMessage(message) {
  if (message.includes('GITHUB_OAUTH_CLIENT_ID')) {
    return '깃허브 OAuth Client ID가 설정되지 않았습니다.'
  }

  if (message.includes('GITHUB_OAUTH_CLIENT_SECRET')) {
    return '깃허브 OAuth Client Secret이 설정되지 않았습니다.'
  }

  if (message.includes('AUTH_JWT_SECRET_KEY')) {
    return 'JWT 비밀키가 설정되지 않았습니다.'
  }

  return message
}

function isGithubCallbackPage() {
  return window.location.pathname === CALLBACK_PATH
}

function clearCallbackUrl() {
  window.history.replaceState({}, document.title, '/')
}

function clearSession() {
  window.localStorage.removeItem(OAUTH_STATE_STORAGE_KEY)
  window.localStorage.removeItem(LEGACY_ACCESS_TOKEN_STORAGE_KEY)
}

export default App
