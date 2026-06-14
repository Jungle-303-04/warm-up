import { useMemo, useState } from 'react'
import './App.css'

const API_BASE_URL = normalizeApiBaseUrl(
  import.meta.env.VITE_API_BASE_URL || '/api',
)
const TOKEN_STORAGE_KEY = 'warm-up.auth.accessToken'
const OAUTH_STATE_STORAGE_KEY = 'warm-up.auth.githubState'
const DEMO_USER = {
  user_id: 0,
  github_user_id: 1000,
  login: 'demo-minjeong',
  name: 'Demo User',
  email: 'demo@example.com',
  avatar_url: '',
}
const EMPTY_STATUS = {
  type: 'muted',
  message: 'Ready',
}

function App() {
  const initialAuth = useMemo(() => readInitialAuthState(), [])
  const [accessToken, setAccessToken] = useState(initialAuth.accessToken)
  const [callbackJson, setCallbackJson] = useState('')
  const [authorizeUrl, setAuthorizeUrl] = useState('')
  const [oauthState, setOauthState] = useState(initialAuth.oauthState)
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState(initialAuth.status)
  const [isLoading, setIsLoading] = useState(false)

  const hasToken = Boolean(accessToken)
  const userLabel = useMemo(() => buildUserLabel(user), [user])

  async function startGithubLogin() {
    setIsLoading(true)
    setStatus({ type: 'muted', message: 'Requesting GitHub authorization' })

    try {
      const payload = await fetchJson(`${API_BASE_URL}/auth/github/login`)
      setAuthorizeUrl(payload.authorize_url)
      setOauthState(payload.state)
      window.localStorage.setItem(OAUTH_STATE_STORAGE_KEY, payload.state)
      setStatus({ type: 'success', message: 'Authorization URL is ready' })
      window.location.assign(payload.authorize_url)
    } catch (error) {
      setStatus({ type: 'error', message: error.message })
    } finally {
      setIsLoading(false)
    }
  }

  async function loadCurrentUser(token = accessToken) {
    if (!validateToken(token, setStatus)) {
      return
    }

    setIsLoading(true)
    setStatus({ type: 'muted', message: 'Checking current session' })

    try {
      const payload = await fetchJson(`${API_BASE_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      setUser(payload.user)
      setStatus({ type: 'success', message: 'Session verified' })
    } catch (error) {
      setUser(null)
      setStatus({ type: 'error', message: error.message })
    } finally {
      setIsLoading(false)
    }
  }

  function applyCallbackJson() {
    try {
      const token = extractAccessToken(callbackJson)
      saveToken(token)
      setAccessToken(token)
      setStatus({ type: 'success', message: 'Token saved' })
      void loadCurrentUser(token)
    } catch (error) {
      setStatus({ type: 'error', message: error.message })
    }
  }

  function applyDemoSession() {
    setUser(DEMO_USER)
    setAccessToken('')
    setAuthorizeUrl('')
    setStatus({ type: 'success', message: 'Demo session is active' })
  }

  function clearSession() {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY)
    window.localStorage.removeItem(OAUTH_STATE_STORAGE_KEY)
    setAccessToken('')
    setCallbackJson('')
    setAuthorizeUrl('')
    setOauthState('')
    setUser(null)
    setStatus(EMPTY_STATUS)
  }

  return (
    <main className="auth-shell">
      <section className="workspace">
        <div className="toolbar">
          <div>
            <p className="eyebrow">Code-Trust Kanban</p>
            <h1>GitHub OAuth Test Console</h1>
          </div>
          <span className={`status-pill ${status.type}`}>{status.message}</span>
        </div>

        <div className="grid">
          <section className="panel auth-panel" aria-labelledby="oauth-title">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Step 1</p>
                <h2 id="oauth-title">OAuth Start</h2>
              </div>
              <button
                type="button"
                className="icon-button"
                onClick={startGithubLogin}
                disabled={isLoading}
                aria-label="Start GitHub OAuth login"
                title="Start GitHub OAuth login"
              >
                <svg aria-hidden="true">
                  <use href="/icons.svg#github-icon" />
                </svg>
              </button>
            </div>

            <dl className="info-list">
              <div>
                <dt>API</dt>
                <dd>{API_BASE_URL}</dd>
              </div>
              <div>
                <dt>State</dt>
                <dd>{oauthState || 'none'}</dd>
              </div>
              <div>
                <dt>Authorize URL</dt>
                <dd>{authorizeUrl || 'none'}</dd>
              </div>
            </dl>

            <div className="actions">
              <button type="button" onClick={startGithubLogin} disabled={isLoading}>
                Start GitHub Login
              </button>
              <button
                type="button"
                className="secondary"
                onClick={applyDemoSession}
                disabled={isLoading}
              >
                Demo Session
              </button>
            </div>
          </section>

          <section className="panel" aria-labelledby="token-title">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Step 2</p>
                <h2 id="token-title">Callback Token</h2>
              </div>
              <span className="token-state">{hasToken ? 'saved' : 'empty'}</span>
            </div>

            <textarea
              value={callbackJson}
              onChange={(event) => setCallbackJson(event.target.value)}
              spellCheck="false"
              placeholder='{"access_token":"...","token_type":"bearer","user":{...}}'
            />

            <div className="actions">
              <button type="button" onClick={applyCallbackJson} disabled={isLoading}>
                Save Token
              </button>
              <button
                type="button"
                className="secondary"
                onClick={() => void loadCurrentUser()}
                disabled={isLoading || !hasToken}
              >
                Verify Session
              </button>
            </div>
          </section>

          <section className="panel user-panel" aria-labelledby="session-title">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Step 3</p>
                <h2 id="session-title">Current User</h2>
              </div>
              <button
                type="button"
                className="secondary compact"
                onClick={clearSession}
                disabled={isLoading}
              >
                Clear
              </button>
            </div>

            <div className="profile">
              <div className="avatar" aria-hidden="true">
                {user?.avatar_url ? (
                  <img src={user.avatar_url} alt="" />
                ) : (
                  <svg>
                    <use href="/icons.svg#github-icon" />
                  </svg>
                )}
              </div>
              <div>
                <p className="profile-name">{userLabel}</p>
                <p className="profile-meta">
                  {user ? `user ${user.user_id} / github ${user.github_user_id}` : 'No active user'}
                </p>
              </div>
            </div>

            <pre className="json-output">{formatJson(user)}</pre>
          </section>
        </div>
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

function extractAccessToken(value) {
  const payload = JSON.parse(value)
  const token = payload.access_token

  if (!token || typeof token !== 'string') {
    throw new Error('access_token is required')
  }

  return token
}

function saveToken(token) {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token)
}

function readTokenFromUrl() {
  const searchParams = new URLSearchParams(window.location.search)
  const hashParams = new URLSearchParams(window.location.hash.replace(/^#/, ''))
  return searchParams.get('access_token') || hashParams.get('access_token') || ''
}

function readInitialAuthState() {
  const tokenFromUrl = readTokenFromUrl()

  if (tokenFromUrl) {
    saveToken(tokenFromUrl)
    return {
      accessToken: tokenFromUrl,
      oauthState: window.localStorage.getItem(OAUTH_STATE_STORAGE_KEY) || '',
      status: { type: 'success', message: 'Token captured from URL' },
    }
  }

  return {
    accessToken: window.localStorage.getItem(TOKEN_STORAGE_KEY) || '',
    oauthState: window.localStorage.getItem(OAUTH_STATE_STORAGE_KEY) || '',
    status: EMPTY_STATUS,
  }
}

function buildUserLabel(user) {
  if (!user) {
    return 'Signed out'
  }

  return user.name || user.login
}

function formatJson(value) {
  return JSON.stringify(value || {}, null, 2)
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

  return `Request failed with ${status}`
}

function validateToken(token, setStatus) {
  if (!token) {
    setStatus({ type: 'error', message: 'Token is required' })
    return false
  }

  return true
}

export default App
