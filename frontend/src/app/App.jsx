import { useCallback, useEffect, useState } from 'react'

import { AuthSection } from '../features/auth/AuthSection'
import { CalendarWorkspace } from '../features/calendar/CalendarWorkspace'
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
  const [boards, setBoards] = useState([])
  const [selectedCalendarEvent, setSelectedCalendarEvent] = useState(null)
  const [visibleMonth, setVisibleMonth] = useState(() => new Date())
  const [isLoadingBoards, setIsLoadingBoards] = useState(false)
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

  const loadBoards = useCallback(async (currentUser) => {
    if (!currentUser?.user_id) {
      setBoards([])
      setSelectedCalendarEvent(null)
      return
    }

    setIsLoadingBoards(true)
    setStatus({ type: 'muted', message: '게시글 일정 데이터를 불러오는 중입니다.' })

    try {
      // Backend: GET /board/
      // Expected query:
      // {
      //   user_id?: number,
      //   title?: string | null,
      //   tag?: string | null,
      //   page: number,
      //   size: number
      // }
      // Response:
      // {
      //   items: Array<{
      //     id: number,
      //     board_type: 1 | 2 | 3,
      //     title: string,
      //     content: string,
      //     tag?: string | null,
      //     user_id: number,
      //     schedule_board_detail?: {
      //       start_at: string,
      //       end_at: string,
      //       importance: number
      //     } | null,
      //     proceedings_board_detail?: {
      //       meeting_date: string
      //     } | null
      //   }>,
      //   total: number,
      //   page: number,
      //   size: number
      // }
      const params = new URLSearchParams({
        user_id: String(currentUser.user_id),
        page: '1',
        size: '100',
      })
      const payload = await fetchJson(`${API_BASE_URL}/board/?${params}`)
      setBoards(payload.items || [])
      setSelectedCalendarEvent(null)
      setStatus({
        type: 'success',
        message: `게시글 ${payload.items?.length || 0}개를 캘린더에 반영했습니다.`,
      })
    } catch (error) {
      setStatus({ type: 'error', message: toKoreanErrorMessage(error.message) })
    } finally {
      setIsLoadingBoards(false)
    }
  }, [])

  const loadAuthenticatedUser = useCallback(async (message, options = {}) => {
    await runAction('auth', message, async () => {
      try {
        const payload = await fetchJson(`${API_BASE_URL}/auth/me`)
        setUser(payload.user)
        setStatus({ type: 'success', message: '깃허브 로그인이 완료되었습니다.' })
        void loadBoards(payload.user)
      } catch (error) {
        if (options.silentUnauthenticated) {
          setStatus(INITIAL_STATUS)
        } else {
          setStatus({ type: 'error', message: toKoreanErrorMessage(error.message) })
        }
        setUser(null)
        setBoards([])
        setSelectedCalendarEvent(null)
      }
    })
  }, [loadBoards, runAction])

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
      setBoards([])
      setSelectedCalendarEvent(null)
      setStatus({ type: 'muted', message: '로그아웃되었습니다.' })
    })
  }

  function showPreviousMonth() {
    setVisibleMonth((current) => {
      const next = new Date(current)
      next.setMonth(current.getMonth() - 1)
      return next
    })
  }

  function showNextMonth() {
    setVisibleMonth((current) => {
      const next = new Date(current)
      next.setMonth(current.getMonth() + 1)
      return next
    })
  }

  function showCurrentMonth() {
    setVisibleMonth(new Date())
  }

  async function openBoardDetail(boardId) {
    setStatus({ type: 'muted', message: '게시글 상세를 불러오는 중입니다.' })

    try {
      // Backend: GET /board/{board_id}
      // Expected path:
      // {
      //   board_id: number
      // }
      // Response:
      // {
      //   id: number,
      //   board_type: 1 | 2 | 3,
      //   title: string,
      //   content: string,
      //   tag?: string | null,
      //   schedule_board_detail?: {
      //     start_at: string,
      //     end_at: string,
      //     importance: number
      //   } | null,
      //   proceedings_board_detail?: {
      //     meeting_date: string
      //   } | null
      // }
      const board = await fetchJson(`${API_BASE_URL}/board/${boardId}`)
      setSelectedCalendarEvent((current) =>
        current
          ? {
              ...current,
              title: board.title,
              content: board.content,
              tag: board.tag,
            }
          : null,
      )
      setStatus({ type: 'success', message: '게시글 상세를 열었습니다.' })
    } catch (error) {
      setStatus({ type: 'error', message: toKoreanErrorMessage(error.message) })
    }
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
    <div className="auth-shell">
      <AuthSection
        user={user}
        status={status}
        oauthState={oauthState}
        isLoading={isLoading}
        onLogin={startGithubLogin}
        onLogout={logout}
      >
        {user ? (
          <>
            <CalendarWorkspace
              boards={boards}
              selectedEvent={selectedCalendarEvent}
              visibleMonth={visibleMonth}
              isLoadingBoards={isLoadingBoards}
              onPreviousMonth={showPreviousMonth}
              onNextMonth={showNextMonth}
              onCurrentMonth={showCurrentMonth}
              onReloadBoards={() => void loadBoards(user)}
              onSelectEvent={setSelectedCalendarEvent}
              onOpenBoard={(boardId) => void openBoardDetail(boardId)}
            />
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
          </>
        ) : null}
      </AuthSection>
    </div>
  )
}

export default App
