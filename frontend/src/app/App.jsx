import { useCallback, useEffect, useState } from 'react'

import { AuthSection } from '../features/auth/AuthSection'
import { BoardCreatePanel } from '../features/board/BoardCreatePanel'
import { BoardDetailPage } from '../features/board/BoardDetailPage'
import { BoardSearchPage } from '../features/board/BoardSearchPage'
import { DEFAULT_BOARD_SEARCH_FILTERS } from '../features/board/boardFilters'
import { CalendarWorkspace } from '../features/calendar/CalendarWorkspace'
import { ChatbotDrawer } from '../features/chatbot/ChatbotDrawer'
import {
  RepositoryRunsPage,
  RepositoryWorkspace,
} from '../features/repository/RepositoryWorkspace'
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
  AUTH_SESSION_HINT_STORAGE_KEY,
  INITIAL_STATUS,
  LEGACY_ACCESS_TOKEN_STORAGE_KEY,
  OAUTH_STATE_STORAGE_KEY,
} from './config'
import './App.css'

const THEME_STORAGE_KEY = 'warm-up-theme'
const BOARD_EVENT_COLOR_STORAGE_KEY = 'warm-up-board-event-colors'

function App() {
  const [status, setStatus] = useState(INITIAL_STATUS)
  const [user, setUser] = useState(null)
  const [theme, setTheme] = useState(getInitialTheme)
  const [repositoryFullName, setRepositoryFullName] = useState('')
  const [branch, setBranch] = useState('')
  const [repositoryBranches, setRepositoryBranches] = useState([])
  const [isLoadingRepositoryBranches, setIsLoadingRepositoryBranches] = useState(false)
  const [repositoryBranchMessage, setRepositoryBranchMessage] = useState('')
  const [indexResult, setIndexResult] = useState(null)
  const [repositoryRuns, setRepositoryRuns] = useState([])
  const [chatSelectedRunIds, setChatSelectedRunIds] = useState([])
  const [boards, setBoards] = useState([])
  const [selectedBoard, setSelectedBoard] = useState(null)
  const [isCreatingBoard, setIsCreatingBoard] = useState(false)
  const [boardCreateInitialDate, setBoardCreateInitialDate] = useState(null)
  const [boardSearchFilters, setBoardSearchFilters] = useState(null)
  const [boardDetailBackFilters, setBoardDetailBackFilters] = useState(null)
  const [isRepositoryPageOpen, setIsRepositoryPageOpen] = useState(false)
  const [isRepositoryRunsPageOpen, setIsRepositoryRunsPageOpen] = useState(false)
  const [visibleMonth, setVisibleMonth] = useState(() => new Date())
  const [isLoadingBoards, setIsLoadingBoards] = useState(false)
  const [isLoadingRepositoryRuns, setIsLoadingRepositoryRuns] = useState(false)
  const [boardAction, setBoardAction] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [activeAction, setActiveAction] = useState('')

  const isIndexing = activeAction === 'index'

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem(THEME_STORAGE_KEY, theme)
  }, [theme])

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
      setBoardCreateInitialDate(null)
      setBoardSearchFilters(null)
      setBoardDetailBackFilters(null)
      setIsRepositoryPageOpen(false)
      setIsRepositoryRunsPageOpen(false)
      return
    }

    setIsLoadingBoards(true)
    setStatus({ type: 'muted', message: '게시글 일정 데이터를 불러오는 중입니다.' })

    try {
      // Backend: GET /board/
      // Expected query:
      // {
      //   title?: string | null,
      //   tag?: string | null, // "#기획 #회의"처럼 #으로 구분된 복수 태그 문자열
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
      //     tag?: string | null, // "#기획 #회의"처럼 #으로 구분된 복수 태그 문자열
      //     user_id: number,
      //     author_display_name?: string | null,
      //     author_login?: string | null,
      //     author_name?: string | null,
      //     created_at: string,
      //     updated_at: string,
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
      setBoards(attachBoardEventColors(payload.items || []))
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
        window.localStorage.setItem(AUTH_SESSION_HINT_STORAGE_KEY, '1')
        setUser(payload.user)
        setStatus({ type: 'success', message: '깃허브 로그인이 완료되었습니다.' })
        void loadBoards(payload.user)
        void loadRepositoryRuns()
        const boardId = parseBoardIdFromHash()
        if (isCreateBoardHash()) {
          setSelectedBoard(null)
          setIsCreatingBoard(true)
          setBoardCreateInitialDate(null)
          setBoardSearchFilters(null)
          setBoardDetailBackFilters(null)
          setIsRepositoryPageOpen(false)
          setIsRepositoryRunsPageOpen(false)
          return
        }

        if (isBoardSearchHash()) {
          setSelectedBoard(null)
          setIsCreatingBoard(false)
          setBoardSearchFilters(DEFAULT_BOARD_SEARCH_FILTERS)
          setBoardDetailBackFilters(null)
          setIsRepositoryPageOpen(false)
          setIsRepositoryRunsPageOpen(false)
          return
        }

        if (isRepositoryHash()) {
          setSelectedBoard(null)
          setIsCreatingBoard(false)
          setBoardSearchFilters(null)
          setBoardDetailBackFilters(null)
          setIsRepositoryPageOpen(true)
          setIsRepositoryRunsPageOpen(false)
          return
        }

        if (isRepositoryRunsHash()) {
          setSelectedBoard(null)
          setIsCreatingBoard(false)
          setBoardSearchFilters(null)
          setBoardDetailBackFilters(null)
          setIsRepositoryPageOpen(false)
          setIsRepositoryRunsPageOpen(true)
          return
        }

        if (boardId) {
          setBoardSearchFilters(null)
          setBoardDetailBackFilters(null)
          setIsRepositoryPageOpen(false)
          setIsRepositoryRunsPageOpen(false)
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
        setRepositoryBranches([])
        setRepositoryBranchMessage('')
        setChatSelectedRunIds([])
        setSelectedBoard(null)
        setIsCreatingBoard(false)
        setBoardCreateInitialDate(null)
        setBoardSearchFilters(null)
        setBoardDetailBackFilters(null)
        setIsRepositoryPageOpen(false)
        setIsRepositoryRunsPageOpen(false)
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
      setRepositoryBranches([])
      setRepositoryBranchMessage('')
      setChatSelectedRunIds([])
      setSelectedBoard(null)
      setIsCreatingBoard(false)
      setBoardCreateInitialDate(null)
      setBoardSearchFilters(null)
      setBoardDetailBackFilters(null)
      setIsRepositoryPageOpen(false)
      setIsRepositoryRunsPageOpen(false)
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
      //   tag?: string | null, // "#기획 #회의"처럼 #으로 구분된 복수 태그 문자열
      //   user_id: number,
      //   author_display_name?: string | null,
      //   author_login?: string | null,
      //   author_name?: string | null,
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
      const board = attachBoardEventColor(await fetchJson(`${API_BASE_URL}/board/${boardId}`))
      setSelectedBoard(board)
      setIsCreatingBoard(false)
      setBoardCreateInitialDate(null)
      setBoardDetailBackFilters(options.backToSearchFilters || null)
      setBoardSearchFilters(null)
      setIsRepositoryPageOpen(false)
      setIsRepositoryRunsPageOpen(false)
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
    setBoardCreateInitialDate(null)
    setIsRepositoryPageOpen(false)
    setIsRepositoryRunsPageOpen(false)
    if (boardDetailBackFilters) {
      setBoardSearchFilters(boardDetailBackFilters)
      setBoardDetailBackFilters(null)
      window.history.replaceState({ boardSearch: true }, '', '#board/search')
      return
    }

    setBoardSearchFilters(null)
    setBoardDetailBackFilters(null)
    window.history.replaceState(null, '', window.location.pathname)
  }

  function returnToMainPage() {
    setSelectedBoard(null)
    setIsCreatingBoard(false)
    setBoardCreateInitialDate(null)
    setBoardSearchFilters(null)
    setBoardDetailBackFilters(null)
    setIsRepositoryPageOpen(false)
    setIsRepositoryRunsPageOpen(false)
    window.history.replaceState(null, '', window.location.pathname)
  }

  function openBoardCreatePage(initialDate = null) {
    setSelectedBoard(null)
    setIsCreatingBoard(true)
    setBoardCreateInitialDate(toValidDateOrNull(initialDate))
    setBoardSearchFilters(null)
    setBoardDetailBackFilters(null)
    setIsRepositoryPageOpen(false)
    setIsRepositoryRunsPageOpen(false)
    window.history.pushState({ boardCreate: true }, '', '#board/new')
  }

  function openBoardSearchPage(filters = DEFAULT_BOARD_SEARCH_FILTERS) {
    setSelectedBoard(null)
    setIsCreatingBoard(false)
    setBoardCreateInitialDate(null)
    setBoardDetailBackFilters(null)
    setIsRepositoryPageOpen(false)
    setIsRepositoryRunsPageOpen(false)
    setBoardSearchFilters({
      ...DEFAULT_BOARD_SEARCH_FILTERS,
      ...filters,
    })
    window.history.pushState({ boardSearch: true }, '', '#board/search')
  }

  function openBoardTagSearch(tag) {
    openBoardSearchPage({
      ...DEFAULT_BOARD_SEARCH_FILTERS,
      tagFilter: tag,
    })
  }

  function openRepositoryAnalysis() {
    setSelectedBoard(null)
    setIsCreatingBoard(false)
    setBoardCreateInitialDate(null)
    setBoardSearchFilters(null)
    setBoardDetailBackFilters(null)
    setIsRepositoryPageOpen(true)
    setIsRepositoryRunsPageOpen(false)
    window.history.pushState({ repositoryPage: true }, '', '#repository/register')
  }

  function openRepositoryRunsPage() {
    setSelectedBoard(null)
    setIsCreatingBoard(false)
    setBoardCreateInitialDate(null)
    setBoardSearchFilters(null)
    setBoardDetailBackFilters(null)
    setIsRepositoryPageOpen(false)
    setIsRepositoryRunsPageOpen(true)
    window.history.pushState({ repositoryRunsPage: true }, '', '#repository/runs')
  }

  function toggleTheme() {
    setTheme((currentTheme) => (currentTheme === 'dark' ? 'light' : 'dark'))
  }

  function selectRepositoryRunFromList(run) {
    selectRepositoryRun(run)
    setSelectedBoard(null)
    setIsCreatingBoard(false)
    setBoardCreateInitialDate(null)
    setBoardSearchFilters(null)
    setBoardDetailBackFilters(null)
    setIsRepositoryPageOpen(true)
    setIsRepositoryRunsPageOpen(false)
    window.history.pushState({ repositoryPage: true }, '', '#repository/register')
  }

  async function createBoard(formPayload, uiOptions = {}) {
    setBoardAction('create')
    setStatus({ type: 'muted', message: '게시글을 등록하는 중입니다.' })

    try {
      // Backend: POST /board/
      // Request DTO:
      // {
      //   board_type: 1 | 2 | 3,
      //   title: string,
      //   content: string,
      //   tag?: string | null, // "#기획 #회의"처럼 #으로 구분된 복수 태그 문자열
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
      // eventColor는 현재 백엔드 DTO에 없는 프론트 전용 표시 값이다.
      // TODO(backend): board.event_color 컬럼을 추가하면 이 값을 API body에 포함해 DB에 저장한다.
      // Logged-in browser requests do not send user_id.
      // The backend resolves board.user_id from the auth cookie's internal DB user id.
      // Response DTO는 GET /board/{board_id}와 같은 BoardResponse이다.
      const createdBoard = attachBoardEventColor(
        await postJson(`${API_BASE_URL}/board/`, formPayload),
        uiOptions.eventColor,
      )
      saveBoardEventColor(createdBoard.id, createdBoard.ui_event_color)
      setBoards((currentBoards) => [createdBoard, ...currentBoards])
      setVisibleMonth(getBoardCalendarFocusDate(createdBoard))
      setIsCreatingBoard(false)
      setBoardCreateInitialDate(null)
      setSelectedBoard(null)
      setBoardSearchFilters(null)
      setBoardDetailBackFilters(null)
      setIsRepositoryPageOpen(false)
      setIsRepositoryRunsPageOpen(false)
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

  async function updateBoardDetail(boardId, formPayload, uiOptions = {}) {
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
      //   tag?: string | null, // "#기획 #회의"처럼 #으로 구분된 복수 태그 문자열
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
      // eventColor는 현재 백엔드 DTO에 없는 프론트 전용 표시 값이다.
      // TODO(backend): board.event_color 컬럼을 추가하면 이 값을 API body에 포함해 DB에 저장한다.
      // Logged-in browser requests do not send user_id.
      // The backend resolves board.user_id from the auth cookie's internal DB user id.
      // Response DTO는 GET /board/{board_id}와 같은 BoardResponse이다.
      const updatedBoard = attachBoardEventColor(
        await putJson(`${API_BASE_URL}/board/${boardId}`, formPayload),
        uiOptions.eventColor,
      )
      saveBoardEventColor(updatedBoard.id, updatedBoard.ui_event_color)
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
      deleteBoardEventColor(boardId)
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

    if (isIndexing) {
      return
    }

    const repositoryName = normalizeRepositoryInput(repositoryFullName)
    if (!repositoryName) {
      const errorMessage = '잘못된 입력 형식입니다.'
      setStatus({ type: 'error', message: errorMessage })
      window.alert(errorMessage)
      return
    }

    await runAction('index', '레포지토리를 등록하는 중입니다.', async () => {
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
      const nextIndexResult = buildIndexResultForUi(payload, latestRun)
      setIndexResult(nextIndexResult)
      setChatSelectedRunIds(nextIndexResult.run_id ? [nextIndexResult.run_id] : [])
      const statusMessage = payload.reused
        ? '이미 등록된 레포지토리입니다.'
        : '레포지토리를 등록했습니다.'
      setStatus({
        type: 'success',
        message: statusMessage,
      })
      window.alert(statusMessage)
    })
  }

  function updateRepositoryFullName(value) {
    setRepositoryFullName(value)
    setBranch('')
    setRepositoryBranches([])
    setRepositoryBranchMessage('')
  }

  function updateBranch(value) {
    setBranch(value)
  }

  function selectRepositoryRun(run) {
    setRepositoryFullName(run.repository_full_name || '')
    setBranch(run.branch || '')
    const nextIndexResult = {
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
    }
    setIndexResult(nextIndexResult)
    setChatSelectedRunIds(run.id ? [run.id] : [])
  }

  useEffect(() => {
    if (!user || !isRepositoryPageOpen) {
      return undefined
    }

    const repositoryName = normalizeRepositoryInput(repositoryFullName)
    if (!repositoryName) {
      return undefined
    }

    let didCancel = false
    const timerId = window.setTimeout(async () => {
      setIsLoadingRepositoryBranches(true)
      setRepositoryBranchMessage('브랜치 목록을 확인하는 중입니다.')

      try {
        // Backend: GET /rag/github/repository/branches
        // Expected query:
        // {
        //   repository_full_name: string // "owner/repo" 또는 GitHub URL
        // }
        // Response DTO:
        // {
        //   repository_full_name: string,
        //   default_branch?: string | null,
        //   branches: Array<{
        //     name: string,
        //     commit_sha: string,
        //     protected: boolean,
        //     is_default: boolean
        //   }>
        // }
        // 브랜치 입력은 datalist라서 사용자가 목록 선택과 직접 입력을 모두 할 수 있다.
        const params = new URLSearchParams({ repository_full_name: repositoryName })
        const payload = await fetchJson(`${API_BASE_URL}/rag/github/repository/branches?${params}`)
        if (didCancel) {
          return
        }

        const branches = payload.branches || []
        setRepositoryBranches(branches)
        setBranch((currentBranch) => currentBranch.trim()
          ? currentBranch
          : payload.default_branch || '')
        setRepositoryBranchMessage(
          branches.length
            ? `브랜치 ${branches.length}개를 불러왔습니다.`
            : '조회된 브랜치가 없습니다.',
        )
      } catch (error) {
        if (didCancel) {
          return
        }

        setRepositoryBranches([])
        setRepositoryBranchMessage(toKoreanErrorMessage(error.message))
      } finally {
        if (!didCancel) {
          setIsLoadingRepositoryBranches(false)
        }
      }
    }, 350)

    return () => {
      didCancel = true
      window.clearTimeout(timerId)
    }
  }, [isRepositoryPageOpen, repositoryFullName, user])

  useEffect(() => {
    const timerId = window.setTimeout(() => {
      window.localStorage.removeItem(LEGACY_ACCESS_TOKEN_STORAGE_KEY)

      if (isGithubCallbackPage()) {
        clearCallbackUrl()
        void loadAuthenticatedUser('깃허브 로그인을 완료하는 중입니다.')
        return
      }

      if (window.localStorage.getItem(AUTH_SESSION_HINT_STORAGE_KEY)) {
        void loadAuthenticatedUser('기존 로그인 상태를 확인하는 중입니다.', {
          silentUnauthenticated: true,
        })
      }
    }, 0)

    return () => window.clearTimeout(timerId)
  }, [loadAuthenticatedUser])

  useEffect(() => {
    function handleBrowserNavigation() {
      const boardId = parseBoardIdFromHash()

      if (isCreateBoardHash()) {
        setSelectedBoard(null)
        setIsCreatingBoard(true)
        setBoardCreateInitialDate(null)
        setBoardSearchFilters(null)
        setBoardDetailBackFilters(null)
        setIsRepositoryPageOpen(false)
        setIsRepositoryRunsPageOpen(false)
        return
      }

      if (isBoardSearchHash()) {
        setSelectedBoard(null)
        setIsCreatingBoard(false)
        setBoardCreateInitialDate(null)
        setBoardSearchFilters(DEFAULT_BOARD_SEARCH_FILTERS)
        setBoardDetailBackFilters(null)
        setIsRepositoryPageOpen(false)
        setIsRepositoryRunsPageOpen(false)
        return
      }

      if (isRepositoryHash()) {
        setSelectedBoard(null)
        setIsCreatingBoard(false)
        setBoardCreateInitialDate(null)
        setBoardSearchFilters(null)
        setBoardDetailBackFilters(null)
        setIsRepositoryPageOpen(true)
        setIsRepositoryRunsPageOpen(false)
        return
      }

      if (isRepositoryRunsHash()) {
        setSelectedBoard(null)
        setIsCreatingBoard(false)
        setBoardCreateInitialDate(null)
        setBoardSearchFilters(null)
        setBoardDetailBackFilters(null)
        setIsRepositoryPageOpen(false)
        setIsRepositoryRunsPageOpen(true)
        return
      }

      if (!boardId) {
        setSelectedBoard(null)
        setIsCreatingBoard(false)
        setBoardCreateInitialDate(null)
        setBoardSearchFilters(null)
        setBoardDetailBackFilters(null)
        setIsRepositoryPageOpen(false)
        setIsRepositoryRunsPageOpen(false)
        return
      }

      setBoardSearchFilters(null)
      setBoardCreateInitialDate(null)
      setBoardDetailBackFilters(null)
      setIsRepositoryPageOpen(false)
      setIsRepositoryRunsPageOpen(false)
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
        onStartCreateBoard={openBoardCreatePage}
        onOpenBoardSearch={() => openBoardSearchPage()}
        onOpenRepositoryAnalysis={openRepositoryAnalysis}
        onOpenRepositoryRuns={openRepositoryRunsPage}
        theme={theme}
        onToggleTheme={toggleTheme}
      >
        {user ? (
          <>
            {selectedBoard ? (
              <BoardDetailPage
                key={`${selectedBoard.id}-${selectedBoard.updated_at}`}
                board={selectedBoard}
                isSaving={Boolean(boardAction)}
                onBack={closeBoardDetail}
                onUpdate={(payload, uiOptions) =>
                  updateBoardDetail(selectedBoard.id, payload, uiOptions)}
                onDelete={() => void deleteBoardDetail(selectedBoard.id)}
                onOpenTagSearch={openBoardTagSearch}
              />
            ) : isCreatingBoard ? (
              <BoardCreatePanel
                key={boardCreateInitialDate?.toISOString() || 'default-create-board'}
                initialStartDate={boardCreateInitialDate}
                isSaving={boardAction === 'create'}
                onCancel={closeBoardDetail}
                onCreate={createBoard}
              />
            ) : boardSearchFilters ? (
              <BoardSearchPage
                key={JSON.stringify(boardSearchFilters)}
                boards={boards}
                initialFilters={boardSearchFilters}
                onBack={returnToMainPage}
                onOpenBoard={(boardId, currentFilters = boardSearchFilters) =>
                  void openBoardDetail(boardId, {
                    backToSearchFilters: currentFilters,
                  })}
              />
            ) : isRepositoryPageOpen ? (
              <RepositoryWorkspace
                repositoryFullName={repositoryFullName}
                branch={branch}
                indexResult={indexResult}
                isLoading={isLoading}
                isIndexing={isIndexing}
                branchOptions={repositoryBranches}
                isLoadingBranches={isLoadingRepositoryBranches}
                branchLookupMessage={repositoryBranchMessage}
                onRepositoryChange={updateRepositoryFullName}
                onBranchChange={updateBranch}
                onIndexRepository={indexRepository}
              />
            ) : isRepositoryRunsPageOpen ? (
              <RepositoryRunsPage
                repositoryRuns={repositoryRuns}
                isLoadingRepositoryRuns={isLoadingRepositoryRuns}
                onReload={() => void loadRepositoryRuns({ notify: true })}
                onSelectRepositoryRun={selectRepositoryRunFromList}
              />
            ) : (
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
            )}
            <ChatbotDrawer
              indexResult={indexResult}
              isIndexing={isIndexing}
              repositoryRuns={repositoryRuns}
              selectedRunIds={chatSelectedRunIds}
              onSelectedRunIdsChange={setChatSelectedRunIds}
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

function isBoardSearchHash() {
  return window.location.hash === '#board/search'
}

function isRepositoryHash() {
  return (
    window.location.hash === '#repository'
    || window.location.hash === '#repository/register'
  )
}

function isRepositoryRunsHash() {
  return window.location.hash === '#repository/runs'
}

function getBoardCalendarFocusDate(board) {
  const calendarDate =
    board.schedule_board_detail?.start_at
    || board.proceedings_board_detail?.meeting_date
    || board.created_at

  return calendarDate ? new Date(calendarDate) : new Date()
}

function attachBoardEventColors(boards) {
  return boards.map((board) => attachBoardEventColor(board))
}

function attachBoardEventColor(board, preferredColor = null) {
  const eventColor = normalizeHexColor(preferredColor)
    || readBoardEventColors()[String(board.id)]
    || null

  return {
    ...board,
    ui_event_color: eventColor,
  }
}

function saveBoardEventColor(boardId, color) {
  const normalizedColor = normalizeHexColor(color)
  if (!normalizedColor) {
    return
  }

  const colors = readBoardEventColors()
  colors[String(boardId)] = normalizedColor
  localStorage.setItem(BOARD_EVENT_COLOR_STORAGE_KEY, JSON.stringify(colors))
}

function deleteBoardEventColor(boardId) {
  const colors = readBoardEventColors()
  delete colors[String(boardId)]
  localStorage.setItem(BOARD_EVENT_COLOR_STORAGE_KEY, JSON.stringify(colors))
}

function readBoardEventColors() {
  try {
    const parsedValue = JSON.parse(
      localStorage.getItem(BOARD_EVENT_COLOR_STORAGE_KEY) || '{}',
    )
    return Object.fromEntries(
      Object.entries(parsedValue).filter(([, color]) => normalizeHexColor(color)),
    )
  } catch {
    return {}
  }
}

function normalizeHexColor(color) {
  return typeof color === 'string' && /^#[0-9a-f]{6}$/i.test(color)
    ? color.toUpperCase()
    : ''
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

function getInitialTheme() {
  const storedTheme = localStorage.getItem(THEME_STORAGE_KEY)
  if (storedTheme === 'dark' || storedTheme === 'light') {
    return storedTheme
  }

  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function toValidDateOrNull(value) {
  if (!(value instanceof Date)) {
    return null
  }

  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

function normalizeRepositoryInput(value) {
  const repository = value.trim()
  let normalizedRepository = repository

  if (!repository) {
    return ''
  }

  if (repository.startsWith('git@github.com:')) {
    normalizedRepository = repository.replace('git@github.com:', '')
  } else if (repository.startsWith('http://') || repository.startsWith('https://')) {
    try {
      const url = new URL(repository)
      if (url.hostname !== 'github.com') {
        return ''
      }
      normalizedRepository = url.pathname.replace(/^\/+|\/+$/g, '')
    } catch {
      return ''
    }
  }

  if (normalizedRepository.endsWith('.git')) {
    normalizedRepository = normalizedRepository.slice(0, -4)
  }

  const parts = normalizedRepository.split('/')
  if (parts.length !== 2) {
    return ''
  }

  const [owner, repo] = parts
  if (!owner || !repo || /\s/.test(owner) || /\s/.test(repo)) {
    return ''
  }

  return `${owner}/${repo}`
}
