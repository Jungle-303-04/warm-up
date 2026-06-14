import { useState } from 'react'
import './App.css'

const API_BASE_URL = normalizeApiBaseUrl(
  import.meta.env.VITE_API_BASE_URL || '/api',
)
const OAUTH_STATE_STORAGE_KEY = 'warm-up.auth.githubState'
const INITIAL_STATUS = {
  type: 'muted',
  message: '로그인 전입니다.',
}

function App() {
  const [status, setStatus] = useState(INITIAL_STATUS)
  const [oauthState, setOauthState] = useState(
    window.localStorage.getItem(OAUTH_STATE_STORAGE_KEY) || '',
  )
  const [authorizeUrl, setAuthorizeUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  async function startGithubLogin() {
    setIsLoading(true)
    setStatus({ type: 'muted', message: '깃허브 로그인 주소를 요청하는 중입니다.' })

    try {
      const payload = await fetchJson(`${API_BASE_URL}/auth/github/login`)
      setOauthState(payload.state)
      setAuthorizeUrl(payload.authorize_url)
      window.localStorage.setItem(OAUTH_STATE_STORAGE_KEY, payload.state)
      setStatus({ type: 'success', message: '깃허브 로그인 페이지로 이동합니다.' })
      window.location.assign(payload.authorize_url)
    } catch (error) {
      setStatus({ type: 'error', message: toKoreanErrorMessage(error.message) })
    } finally {
      setIsLoading(false)
    }
  }

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
          <h1 id="login-title">깃허브로 로그인하세요</h1>
          <p>
            레포지토리 코드와 보드 계획을 비교하려면 먼저 깃허브 권한이
            필요합니다.
          </p>
        </div>

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

        <div className={`status-box ${status.type}`} role="status">
          {status.message}
        </div>

        <dl className="connection-list">
          <div>
            <dt>API 주소</dt>
            <dd>{API_BASE_URL}</dd>
          </div>
          <div>
            <dt>상태 토큰</dt>
            <dd>{oauthState || '아직 발급되지 않음'}</dd>
          </div>
          <div>
            <dt>깃허브 인증 주소</dt>
            <dd>{authorizeUrl || '아직 요청하지 않음'}</dd>
          </div>
        </dl>
      </section>
    </main>
  )
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
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

export default App
