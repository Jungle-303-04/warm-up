import { useCallback, useEffect, useState } from 'react'

import { AuthSection } from '../features/auth/AuthSection'
import { BoardCreatePanel } from '../features/board/BoardCreatePanel'
import { BoardDetailPage } from '../features/board/BoardDetailPage'
import { CalendarWorkspace } from '../features/calendar/CalendarWorkspace'
import { ChatbotDrawer } from '../features/chatbot/ChatbotDrawer'
import { RepositoryWorkspace } from '../features/repository/RepositoryWorkspace'
import {
  deleteJson,
  fetchJson,
  postJson,
  putJson,
  toKoreanErrorMessage,
} from '../shared/api/http'
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
  const [user, setUser] = useState(null)
  const [repositoryFullName, setRepositoryFullName] = useState('')
  const [branch, setBranch] = useState('')
  const [indexResult, setIndexResult] = useState(null)
  const [repositoryRuns, setRepositoryRuns] = useState([])
  const [boards, setBoards] = useState([])
  const [selectedBoard, setSelectedBoard] = useState(null)
  const [isCreatingBoard, setIsCreatingBoard] = useState(false)
  const [visibleMonth, setVisibleMonth] = useState(() => new Date())
  const [isLoadingBoards, setIsLoadingBoards] = useState(false)
  const [isLoadingRepositoryRuns, setIsLoadingRepositoryRuns] = useState(false)
  const [boardAction, setBoardAction] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [activeAction, setActiveAction] = useState('')

  const isIndexing = activeAction === 'index'

  const runAction = useCallback(async (action, message, callback) => {
    setIsLoading(true)
    setActiveAction(action)
    setStatus({ type: 'muted', message })

    try {
      await callback()
    } catch (error) {
      const errorMessage = toKoreanErrorMessage(error.message)
      setStatus({ type: 'error', message: errorMessage })

      if (action !== 'auth' && action !== 'login') {
        window.alert(errorMessage)
      }
    } finally {
      setIsLoading(false)
      setActiveAction('')
    }
  }, [])

  const loadRepositoryRuns = useCallback(async (options = {}) => {
    setIsLoadingRepositoryRuns(true)

    try {
      // Backend: GET /rag/runs
      // Expected query:
      // {
      //   limit: number
      // }
      // Response DTO:
      // {
      //   items: Array<{
      //     id: number,
      //     repository_full_name?: string | null,
      //     branch?: string | null,
      //     commit_sha: string,
      //     indexed_at: string,
      //     total_files: number,
      //     indexed_files: number,
      //     skipped_files: number,
      //     total_chunks: number
      //   }>,
      //   total: number
      // }
      // 화면에서는 repository_full_name + branch 기준 최신 indexed_at만 보여준다.
      const payload = await fetchJson(`${API_BASE_URL}/rag/runs?limit=50`)
      const latestRuns = buildLatestRepositoryRuns(payload.items || [])
      setRepositoryRuns(latestRuns)

      if (options.notify) {
        window.alert('분석된 레포지토리 목록을 새로고침했습니다.')
      }

      return latestRuns
    } catch (error) {
      const errorMessage = toKoreanErrorMessage(error.message)
      if (options.notify) {
        setStatus({ type: 'error', message: errorMessage })
        window.alert(errorMessage)
      }
      return []
    } finally {
      setIsLoadingRepositoryRuns(false)
    }
  }, [])

  async function startGithubLogin() {
    await runAction('login', '깃허브 로그인 주소를 요청하는 중입니다.', async () => {
      // Backend: GET /auth/github/login
      // Request body 없음.
      // Response DTO:
      // {
      //   authorize_url: string,
      //   state: string,
      //   scope: string
      // }
      // state는 OAuth callback 검증용으로 브라우저 localStorage에 잠시 보관한다.
      const payload = await fetchJson(`${API_BASE_URL}/auth/github/login`)
      window.localStorage.setItem(OAUTH_STATE_STORAGE_KEY, payload.state)
      setStatus({ type: 'success', message: '깃허브 로그인 페이지로 이동합니다.' })
      window.location.assign(payload.authorize_url)
    })
  }

  const loadBoards = useCallback(async (currentUser, options = {}) => {
    if (!currentUser?.user_id) {
      setBoards([])
      setIsCreatingBoard(false)
      return
    }

    setIsLoadingBoards(true)
    setStatus({ type: 'muted', message: '게시글 일정 데이터를 불러오는 중입니다.' })

    try {
      // Backend: GET /board/
      // Expected query:
      // {
      //   title?: string | null,
      //   tag?: string | null,
      //   page: number,
      //   size: number
      // }
      // Logged-in browser requests do not send user_id.
      // The backend resolves board.user_id from the auth cookie's internal DB user id.
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
        page: '1',
        size: '100',
      })
      const payload = await fetchJson(`${API_BASE_URL}/board/?${params}`)
      setBoards(payload.items || [])
      const successMessage = `게시글 ${payload.items?.length || 0}개를 캘린더에 반영했습니다.`
      setStatus({ type: 'success', message: successMessage })

      if (options.notify) {
        window.alert(successMessage)
      }
    } catch (error) {
      const errorMessage = toKoreanErrorMessage(error.message)
      setStatus({ type: 'error', message: errorMessage })

      if (options.notify) {
        window.alert(errorMessage)
      }
    } finally {
      setIsLoadingBoards(false)
    }
  }, [])

  const loadAuthenticatedUser = useCallback(async (message, options = {}) => {
    await runAction('auth', message, async () => {
      try {
        // Backend: GET /auth/me
        // Request body 없음. 브라우저가 auth cookie를 credentials: include로 함께 보낸다.
        // Response DTO:
        // {
        //   user: {
        //     user_id: number,
        //     github_user_id: number,
        //     login: string,
        //     name?: string | null,
        //     email?: string | null,
        //     avatar_url?: string | null
        //   }
        // }
        // user_id는 DB 내부 사용자 id이고, board.user_id와 매칭되는 기준이다.
        const payload = await fetchJson(`${API_BASE_URL}/auth/me`)
        setUser(payload.user)
        setStatus({ type: 'success', message: '깃허브 로그인이 완료되었습니다.' })
        void loadBoards(payload.user)
        void loadRepositoryRuns()
        const boardId = parseBoardIdFromHash()
        if (isCreateBoardHash()) {
          setSelectedBoard(null)
          setIsCreatingBoard(true)
          return
        }

        if (boardId) {
          void openBoardDetail(boardId, { pushUrl: false })
        }
      } catch (error) {
        if (options.silentUnauthenticated) {
          setStatus(INITIAL_STATUS)
        } else {
          setStatus({ type: 'error', message: toKoreanErrorMessage(error.message) })
        }
        setUser(null)
        setBoards([])
        setRepositoryRuns([])
        setSelectedBoard(null)
        setIsCreatingBoard(false)
      }
    })
  }, [loadBoards, loadRepositoryRuns, runAction])

  async function logout() {
    await runAction('logout', '로그아웃하는 중입니다.', async () => {
      // Backend: POST /auth/logout
      // Request body 없음. 서버가 auth cookie를 만료시키는 응답을 내려준다.
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      }).catch(() => undefined)

      clearSession()
      setUser(null)
      setIndexResult(null)
      setBoards([])
      setRepositoryRuns([])
      setSelectedBoard(null)
      setIsCreatingBoard(false)
      window.history.replaceState(null, '', window.location.pathname)
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

  async function openBoardDetail(boardId, options = {}) {
    const shouldPushUrl = options.pushUrl ?? true

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
      //   user_id: number,
      //   created_at: string,
      //   updated_at: string,
      //   assignee_user_ids: number[],
      //   participant_user_ids: number[],
      //   carbon_copy_user_ids: number[],
      //   schedule_board_detail?: {
      //     start_at: string,
      //     end_at: string,
      //     importance: number
      //   } | null,
      //   schedule_board_tasks?: Array<{
      //     id: number,
      //     task_name: string,
      //     task_status: 1 | 2 | 3 | 4
      //   }> | null,
      //   proceedings_board_detail?: {
      //     meeting_date: string
      //   } | null
      // }
      const board = await fetchJson(`${API_BASE_URL}/board/${boardId}`)
      setSelectedBoard(board)
      if (shouldPushUrl) {
        window.history.pushState({ boardId }, '', `#board/${boardId}`)
      }
      setStatus({ type: 'success', message: '게시글 상세를 열었습니다.' })
    } catch (error) {
      setStatus({ type: 'error', message: toKoreanErrorMessage(error.message) })
    }
  }

  function closeBoardDetail() {
    setSelectedBoard(null)
    setIsCreatingBoard(false)
    window.history.replaceState(null, '', window.location.pathname)
  }

  function returnToMainPage() {
    setSelectedBoard(null)
    setIsCreatingBoard(false)
    window.history.replaceState(null, '', window.location.pathname)
  }

  function openBoardCreatePage() {
    setSelectedBoard(null)
    setIsCreatingBoard(true)
    window.history.pushState({ boardCreate: true }, '', '#board/new')
  }

  async function createBoard(formPayload) {
    setBoardAction('create')
    setStatus({ type: 'muted', message: '게시글을 등록하는 중입니다.' })

    try {
      // Backend: POST /board/
      // Request DTO:
      // {
      //   board_type: 1 | 2 | 3,
      //   title: string,
      //   content: string,
      //   tag?: string | null,
      //   assignee_user_ids: number[],
      //   participant_user_ids: number[],
      //   carbon_copy_user_ids: number[],
      //   schedule_board_detail?: {
      //     start_at: string,
      //     end_at: string,
      //     importance: number
      //   } | null,
      //   schedule_board_tasks: Array<{
      //     task_name: string,
      //     task_status: 1 | 2 | 3 | 4
      //   }>,
      //   proceedings_board_detail?: {
      //     meeting_date: string
      //   } | null
      // }
      // Logged-in browser requests do not send user_id.
      // The backend resolves board.user_id from the auth cookie's internal DB user id.
      // Response DTO는 GET /board/{board_id}와 같은 BoardResponse이다.
      const createdBoard = await postJson(`${API_BASE_URL}/board/`, formPayload)
      setBoards((currentBoards) => [createdBoard, ...currentBoards])
      setVisibleMonth(getBoardCalendarFocusDate(createdBoard))
      setIsCreatingBoard(false)
      setSelectedBoard(null)
      window.history.replaceState(null, '', window.location.pathname)
      setStatus({ type: 'success', message: '게시글을 캘린더에 반영했습니다.' })
      window.alert('게시글을 캘린더에 반영했습니다.')
      return true
    } catch (error) {
      const errorMessage = toKoreanErrorMessage(error.message)
      setStatus({ type: 'error', message: errorMessage })
      window.alert(errorMessage)
      return false
    } finally {
      setBoardAction('')
    }
  }

  async function updateBoardDetail(boardId, formPayload) {
    setBoardAction('update')
    setStatus({ type: 'muted', message: '게시글을 수정하는 중입니다.' })

    try {
      // Backend: PUT /board/{board_id}
      // Expected path:
      // {
      //   board_id: number
      // }
      // Request DTO:
      // {
      //   board_type: 1 | 2 | 3,
      //   title: string,
      //   content: string,
      //   tag?: string | null,
      //   assignee_user_ids: number[],
      //   participant_user_ids: number[],
      //   carbon_copy_user_ids: number[],
      //   schedule_board_detail?: {
      //     start_at: string,
      //     end_at: string,
      //     importance: number
      //   } | null,
      //   schedule_board_tasks: Array<{
      //     task_name: string,
      //     task_status: 1 | 2 | 3 | 4
      //   }>,
      //   proceedings_board_detail?: {
      //     meeting_date: string
      //   } | null
      // }
      // Logged-in browser requests do not send user_id.
      // The backend resolves board.user_id from the auth cookie's internal DB user id.
      // Response DTO는 GET /board/{board_id}와 같은 BoardResponse이다.
      const updatedBoard = await putJson(`${API_BASE_URL}/board/${boardId}`, formPayload)
      setSelectedBoard(updatedBoard)
      setBoards((currentBoards) =>
        currentBoards.map((board) => (
          board.id === updatedBoard.id ? updatedBoard : board
        )),
      )
      setStatus({ type: 'success', message: '게시글을 수정했습니다.' })
      window.alert('게시글을 수정했습니다.')
      return true
    } catch (error) {
      const errorMessage = toKoreanErrorMessage(error.message)
      setStatus({ type: 'error', message: errorMessage })
      window.alert(errorMessage)
      return false
    } finally {
      setBoardAction('')
    }
  }

  async function deleteBoardDetail(boardId) {
    setBoardAction('delete')
    setStatus({ type: 'muted', message: '게시글을 삭제하는 중입니다.' })

    try {
      // Backend: DELETE /board/{board_id}
      // Expected path:
      // {
      //   board_id: number
      // }
      // Request body 없음.
      // Logged-in browser requests do not send user_id.
      // The backend checks ownership from the auth cookie's internal DB user id.
      // Response body 없음. 성공하면 HTTP 204.
      await deleteJson(`${API_BASE_URL}/board/${boardId}`)
      setBoards((currentBoards) => currentBoards.filter((board) => board.id !== boardId))
      closeBoardDetail()
      setStatus({ type: 'success', message: '게시글을 삭제했습니다.' })
      window.alert('게시글을 삭제했습니다.')
    } catch (error) {
      const errorMessage = toKoreanErrorMessage(error.message)
      setStatus({ type: 'error', message: errorMessage })
      window.alert(errorMessage)
    } finally {
      setBoardAction('')
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
      // Backend: POST /rag/github/repository/index/store
      // Request DTO:
      // {
      //   repository_full_name: string, // "owner/repo"
      //   branch?: string | null
      // }
      // Response DTO:
      // {
      //   run_id: number,
      //   reused: boolean,
      //   repository_full_name?: string | null,
      //   branch?: string | null,
      //   commit_sha: string,
      //   vector_collection: string,
      //   sql_chunk_count: number,
      //   vector_chunk_count: number,
      //   pipeline_result?: object | null
      // }
      // 이후 질문 요청에서는 commit_sha를 같은 분석 결과 안에서 검색하는 근거 범위로 사용한다.
      const payload = await postJson(
        `${API_BASE_URL}/rag/github/repository/index/store`,
        {
          repository_full_name: repositoryName,
          branch: branch.trim() || null,
        },
      )
      const latestRuns = await loadRepositoryRuns()
      const latestRun = findRepositoryRunByIndexResult(latestRuns, payload)
      setIndexResult(buildIndexResultForUi(payload, latestRun))
      const statusMessage = payload.reused
        ? '이미 분석된 레포지토리 정보를 재사용했습니다.'
        : '레포지토리 분석 정보를 저장했습니다.'
      setStatus({
        type: 'success',
        message: statusMessage,
      })
      window.alert(statusMessage)
    })
  }

  function updateRepositoryFullName(value) {
    setRepositoryFullName(value)
    setIndexResult(null)
  }

  function updateBranch(value) {
    setBranch(value)
    setIndexResult(null)
  }

  function selectRepositoryRun(run) {
    setRepositoryFullName(run.repository_full_name || '')
    setBranch(run.branch || '')
    setIndexResult({
      run_id: run.id,
      reused: true,
      repository_full_name: run.repository_full_name,
      branch: run.branch,
      commit_sha: run.commit_sha,
      vector_collection: '',
      sql_chunk_count: run.total_chunks,
      vector_chunk_count: run.total_chunks,
      pipeline_result: null,
      indexed_at: run.indexed_at,
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

  useEffect(() => {
    function handleBrowserNavigation() {
      const boardId = parseBoardIdFromHash()

      if (isCreateBoardHash()) {
        setSelectedBoard(null)
        setIsCreatingBoard(true)
        return
      }

      if (!boardId) {
        setSelectedBoard(null)
        setIsCreatingBoard(false)
        return
      }

      void openBoardDetail(boardId, { pushUrl: false })
    }

    window.addEventListener('popstate', handleBrowserNavigation)
    return () => window.removeEventListener('popstate', handleBrowserNavigation)
  }, [])

  return (
    <div className="auth-shell">
      <AuthSection
        user={user}
        status={status}
        isLoading={isLoading}
        onLogin={startGithubLogin}
        onLogout={logout}
        onHome={returnToMainPage}
      >
        {user ? (
          <>
            {selectedBoard ? (
              <BoardDetailPage
                key={`${selectedBoard.id}-${selectedBoard.updated_at}`}
                board={selectedBoard}
                isSaving={Boolean(boardAction)}
                onBack={closeBoardDetail}
                onUpdate={(payload) => updateBoardDetail(selectedBoard.id, payload)}
                onDelete={() => void deleteBoardDetail(selectedBoard.id)}
              />
            ) : isCreatingBoard ? (
              <BoardCreatePanel
                isSaving={boardAction === 'create'}
                onCancel={closeBoardDetail}
                onCreate={createBoard}
              />
            ) : (
              <>
                <CalendarWorkspace
                  boards={boards}
                  visibleMonth={visibleMonth}
                  isLoadingBoards={isLoadingBoards}
                  onPreviousMonth={showPreviousMonth}
                  onNextMonth={showNextMonth}
                  onCurrentMonth={showCurrentMonth}
                  onReloadBoards={() => void loadBoards(user, { notify: true })}
                  onStartCreateBoard={openBoardCreatePage}
                  onOpenBoard={(boardId) => void openBoardDetail(boardId)}
                />
                <RepositoryWorkspace
                  repositoryFullName={repositoryFullName}
                  branch={branch}
                  indexResult={indexResult}
                  repositoryRuns={repositoryRuns}
                  isLoading={isLoading}
                  isIndexing={isIndexing}
                  isLoadingRepositoryRuns={isLoadingRepositoryRuns}
                  onRepositoryChange={updateRepositoryFullName}
                  onBranchChange={updateBranch}
                  onIndexRepository={indexRepository}
                  onReloadRepositoryRuns={() => void loadRepositoryRuns({ notify: true })}
                  onSelectRepositoryRun={selectRepositoryRun}
                />
              </>
            )}
            <ChatbotDrawer
              repositoryFullName={repositoryFullName}
              branch={branch}
              indexResult={indexResult}
            />
          </>
        ) : null}
      </AuthSection>
    </div>
  )
}

export default App

function parseBoardIdFromHash() {
  const match = window.location.hash.match(/^#board\/(\d+)$/)
  return match ? Number(match[1]) : null
}

function isCreateBoardHash() {
  return window.location.hash === '#board/new'
}

function getBoardCalendarFocusDate(board) {
  const calendarDate =
    board.schedule_board_detail?.start_at
    || board.proceedings_board_detail?.meeting_date
    || board.created_at

  return calendarDate ? new Date(calendarDate) : new Date()
}

function buildLatestRepositoryRuns(runs) {
  const latestRuns = new Map()

  for (const run of runs) {
    if (!run.repository_full_name) {
      continue
    }

    const key = `${run.repository_full_name}:${run.branch || ''}`
    const currentRun = latestRuns.get(key)

    if (!currentRun || new Date(run.indexed_at) > new Date(currentRun.indexed_at)) {
      latestRuns.set(key, run)
    }
  }

  return Array.from(latestRuns.values()).sort(
    (left, right) => new Date(right.indexed_at) - new Date(left.indexed_at),
  )
}

function findRepositoryRunByIndexResult(runs, indexResult) {
  return runs.find((run) => run.id === indexResult.run_id) || null
}

function buildIndexResultForUi(indexResult, latestRun) {
  return {
    ...indexResult,
    indexed_at: latestRun?.indexed_at || null,
  }
}
