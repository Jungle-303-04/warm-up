import { useCallback, useEffect, useState } from 'react'

import { AuthSection } from '../features/auth/AuthSection'
import { RepositoryWorkspace } from '../features/repository/RepositoryWorkspace'
import { fetchJson, postJson, toKoreanErrorMessage } from '../shared/api/http'
import {
  clearCallbackUrl,
  clearSession,
  isGithubCallbackPage,
} from '../shared/auth/session'
import {
  API_BASE_URL,
  INITIAL_STATUS,
  LEGACY_ACCESS_TOKEN_STORAGE_KEY,
  OAUTH_STATE_STORAGE_KEY,
} from './config'
import './App.css'

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

  const runAction = useCallback(async (action, message, callback) => {
    setIsLoading(true)
    setActiveAction(action)
    setStatus({ type: 'muted', message })

    try {
      await callback()
    } catch (error) {
      setStatus({ type: 'error', message: toKoreanErrorMessage(error.message) })
    } finally {
      setIsLoading(false)
      setActiveAction('')
    }
  }, [])

  async function startGithubLogin() {
    await runAction('login', '깃허브 로그인 주소를 요청하는 중입니다.', async () => {
      const payload = await fetchJson(`${API_BASE_URL}/auth/github/login`)
      setOauthState(payload.state)
      window.localStorage.setItem(OAUTH_STATE_STORAGE_KEY, payload.state)
      setStatus({ type: 'success', message: '깃허브 로그인 페이지로 이동합니다.' })
      window.location.assign(payload.authorize_url)
    })
  }

  const loadAuthenticatedUser = useCallback(async (message, options = {}) => {
    await runAction('auth', message, async () => {
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
      }
    })
  }, [runAction])

  async function logout() {
    await runAction('logout', '로그아웃하는 중입니다.', async () => {
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
    })
  }

  async function indexRepository(event) {
    event.preventDefault()

    const repositoryName = repositoryFullName.trim()
    if (!repositoryName.includes('/')) {
      setStatus({
        type: 'error',
        message: '레포지토리는 owner/repo 형식으로 입력해 주세요.',
      })
      return
    }

    await runAction('index', '레포지토리를 분석하고 DB에 저장하는 중입니다.', async () => {
      setAnswerResult(null)
      const payload = await postJson(
        `${API_BASE_URL}/rag/github/repository/index/store`,
        {
          repository_full_name: repositoryName,
          branch: branch.trim() || null,
        },
      )
      setIndexResult(payload)
      const statusMessage = payload.reused
        ? `이미 분석된 커밋을 재사용합니다: SQL ${payload.sql_chunk_count}개, Vector ${payload.vector_chunk_count}개`
        : `분석 완료: SQL ${payload.sql_chunk_count}개, Vector ${payload.vector_chunk_count}개 저장`
      setStatus({
        type: 'success',
        message: statusMessage,
      })
    })
  }

  function updateRepositoryFullName(value) {
    setRepositoryFullName(value)
    setIndexResult(null)
    setAnswerResult(null)
  }

  function updateBranch(value) {
    setBranch(value)
    setIndexResult(null)
    setAnswerResult(null)
  }

  async function askRepository(event) {
    event.preventDefault()

    if (!indexResult) {
      setStatus({ type: 'error', message: '먼저 레포지토리 분석을 실행해 주세요.' })
      return
    }

    const repositoryName = repositoryFullName.trim()
    await runAction('ask', '저장된 근거로 답변을 생성하는 중입니다.', async () => {
      const payload = await postJson(`${API_BASE_URL}/rag/ask`, {
        question,
        repository_full_name: repositoryName,
        branch: branch.trim() || null,
        commit_sha: indexResult.commit_sha || indexResult.pipeline_result?.commit_sha || null,
        limit: 5,
      })
      setAnswerResult(payload)
      setStatus({ type: 'success', message: 'LLM 액션이 완료되었습니다.' })
    })
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
  }, [loadAuthenticatedUser])

  return (
    <main className="auth-shell">
      <AuthSection
        user={user}
        status={status}
        oauthState={oauthState}
        isLoading={isLoading}
        onLogin={startGithubLogin}
        onLogout={logout}
      >
        {user ? (
          <RepositoryWorkspace
            repositoryFullName={repositoryFullName}
            branch={branch}
            indexResult={indexResult}
            question={question}
            answerResult={answerResult}
            isLoading={isLoading}
            isIndexing={isIndexing}
            isAsking={isAsking}
            onRepositoryChange={updateRepositoryFullName}
            onBranchChange={updateBranch}
            onQuestionChange={setQuestion}
            onIndexRepository={indexRepository}
            onAskRepository={askRepository}
          />
        ) : null}
      </AuthSection>
    </main>
  )
}

export default App
