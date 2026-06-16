import { useEffect, useMemo, useRef, useState } from 'react'

const INITIAL_SESSION_ID = 1
const MOCK_RESPONSE_DELAY_MS = 900

export function ChatbotDrawer({
  indexResult,
  isIndexing,
  repositoryRuns,
  selectedRunIds = [],
  onSelectedRunIdsChange = () => undefined,
}) {
  const responseTimerIds = useRef(new Map())
  const messagesEndRef = useRef(null)
  const selectedRunIdsSignatureRef = useRef(createRunIdsSignature(selectedRunIds))
  const sessionIdRef = useRef(INITIAL_SESSION_ID + 1)
  const messageIdRef = useRef(100)
  const [isOpen, setIsOpen] = useState(false)
  const [draft, setDraft] = useState('')
  const [draftError, setDraftError] = useState('')
  const [isBasisPickerOpen, setIsBasisPickerOpen] = useState(false)
  const [activeSessionId, setActiveSessionId] = useState(INITIAL_SESSION_ID)
  const [sessions, setSessions] = useState(() => [
    createChatSession(INITIAL_SESSION_ID, '새 대화'),
  ])
  const chatBasisOptions = useMemo(
    () => buildChatBasisOptions(repositoryRuns, indexResult),
    [repositoryRuns, indexResult],
  )
  const selectedRuns = useMemo(
    () => chatBasisOptions.filter((run) => selectedRunIds.includes(run.id)),
    [chatBasisOptions, selectedRunIds],
  )

  const chatContext = useMemo(
    () => buildChatContext(selectedRuns, isIndexing),
    [selectedRuns, isIndexing],
  )
  const activeSession = sessions.find((session) => session.id === activeSessionId)
    || sessions[0]
  const messages = activeSession?.messages || []
  const isChatInputDisabled = activeSession.isGenerating
  const hasMultipleSessions = sessions.length > 1

  useEffect(() => () => {
    responseTimerIds.current.forEach((timerId) => window.clearTimeout(timerId))
    responseTimerIds.current.clear()
  }, [])

  useEffect(() => {
    document.body.classList.toggle('chatbot-drawer-open', isOpen)

    return () => {
      document.body.classList.remove('chatbot-drawer-open')
    }
  }, [isOpen])

  useEffect(() => {
    if (!isOpen) {
      return
    }

    messagesEndRef.current?.scrollIntoView({ block: 'end' })
  }, [activeSessionId, messages.length, activeSession.isGenerating, isOpen])

  useEffect(() => {
    const nextSignature = createRunIdsSignature(selectedRunIds)
    if (selectedRunIdsSignatureRef.current === nextSignature) {
      return
    }

    selectedRunIdsSignatureRef.current = nextSignature
    const basisMessage = {
      id: messageIdRef.current,
      sender: 'system',
      text: buildBasisChangedMessage(selectedRuns),
    }
    messageIdRef.current += 1

    setSessions((currentSessions) =>
      currentSessions.map((session) => {
        if (session.id !== activeSessionId) {
          return session
        }

        return {
          ...session,
          updatedAt: new Date().toISOString(),
          messages: [
            ...session.messages,
            basisMessage,
          ],
        }
      }),
    )
  }, [activeSessionId, selectedRunIds, selectedRuns])

  function createNewSession() {
    const nextSession = createChatSession(sessionIdRef.current, '새 대화')
    sessionIdRef.current += 1
    setSessions((currentSessions) => [nextSession, ...currentSessions])
    setActiveSessionId(nextSession.id)
    setDraft('')
    setDraftError('')
  }

  function openDrawer() {
    setIsOpen(true)
    setDraftError('')
  }

  function closeDrawer() {
    setIsOpen(false)
    setDraftError('')
  }

  function toggleBasisPicker() {
    setIsBasisPickerOpen((current) => !current)
    setDraftError('')
  }

  function selectConversationBasis() {
    onSelectedRunIdsChange([])
    setDraftError('')
  }

  function deleteSession(sessionId) {
    const timerId = responseTimerIds.current.get(sessionId)
    if (timerId) {
      window.clearTimeout(timerId)
      responseTimerIds.current.delete(sessionId)
    }

    if (sessions.length === 1) {
      const nextSession = createChatSession(sessionIdRef.current, '새 대화')
      sessionIdRef.current += 1
      setSessions([nextSession])
      setActiveSessionId(nextSession.id)
      setDraft('')
      setDraftError('')
      return
    }

    const nextSessions = sessions.filter((session) => session.id !== sessionId)
    setSessions(nextSessions)

    if (sessionId === activeSessionId) {
      setActiveSessionId(nextSessions[0].id)
      setDraft('')
      setDraftError('')
    }
  }

  function submitMockMessage(event) {
    event.preventDefault()
    sendMockMessage()
  }

  function toggleSelectedRun(runId) {
    onSelectedRunIdsChange(
      selectedRunIds.includes(runId)
        ? selectedRunIds.filter((currentRunId) => currentRunId !== runId)
        : [...selectedRunIds, runId],
    )
    setDraftError('')
  }

  function sendMockMessage() {
    const nextQuestion = draft.trim()
    if (!nextQuestion) {
      setDraftError('질문을 입력한 뒤 보내기를 눌러 주세요.')
      return
    }

    if (isChatInputDisabled) {
      return
    }

    // Future backend connection:
    // POST /rag/ask 또는 별도 chatbot session endpoint로 연결한다.
    // Expected request DTO per session:
    // {
    //   session_id: number | string,
    //   question: string,
    //   selected_runs?: Array<{
    //     run_id: number,
    //     repository_full_name: string,
    //     branch?: string | null,
    //     commit_sha?: string
    //   }>,
    //   limit: number
    // }
    // Backend에서 받아야 하는 정보:
    // - 사용자의 질문과 대화 맥락에서 레포를 추론한 뒤 가장 최신 완료 run을 찾는 결과
    // - 사용자가 선택한 레포가 있으면 여러 selected_runs를 기준으로 검색하는 기능
    // - 선택된 레포가 없으면 질문에 나온 레포명으로 최신 pulling/run_id를 찾는 기능
    // - 새 분석이 진행 중인지 여부와 진행 중인 요청의 repository_full_name/branch
    // 현재는 App이 가진 repositoryRuns/indexResult와 isIndexing으로 더미처럼 동작하게 만든다.
    // Current implementation is a frontend mock, so session/message state stays in React only.
    // Real backend connection should keep the loading state until the API response arrives.
    const userMessage = {
      id: messageIdRef.current,
      sender: 'user',
      text: nextQuestion,
    }
    messageIdRef.current += 1
    const assistantMessage = {
      id: messageIdRef.current,
      sender: 'assistant',
      text: buildMockAssistantText(chatContext),
    }
    messageIdRef.current += 1

    setSessions((currentSessions) =>
      currentSessions.map((session) => {
        if (session.id !== activeSession.id) {
          return session
        }

        return {
          ...session,
          isGenerating: true,
          title: resolveSessionTitle(session, nextQuestion),
          updatedAt: new Date().toISOString(),
          messages: [
            ...session.messages,
            userMessage,
          ],
        }
      }),
    )
    setDraft('')
    setDraftError('')
    scheduleMockResponse(activeSession.id, assistantMessage)
  }

  function submitOnEnter(event) {
    if (event.key !== 'Enter' || event.shiftKey) {
      return
    }

    event.preventDefault()
    sendMockMessage()
  }

  function scheduleMockResponse(sessionId, assistantMessage) {
    const existingTimerId = responseTimerIds.current.get(sessionId)
    if (existingTimerId) {
      window.clearTimeout(existingTimerId)
    }

    const timerId = window.setTimeout(() => {
      setSessions((currentSessions) =>
        currentSessions.map((session) => {
          if (session.id !== sessionId) {
            return session
          }

          return {
            ...session,
            isGenerating: false,
            updatedAt: new Date().toISOString(),
            messages: [
              ...session.messages,
              assistantMessage,
            ],
          }
        }),
      )
      responseTimerIds.current.delete(sessionId)
    }, MOCK_RESPONSE_DELAY_MS)

    responseTimerIds.current.set(sessionId, timerId)
  }

  return (
    <>
      <button
        type="button"
        className="chatbot-launcher"
        onClick={openDrawer}
        aria-label="챗봇 열기"
        aria-controls="rag-chatbot-drawer"
        aria-expanded={isOpen}
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M5 6.5A3.5 3.5 0 0 1 8.5 3h7A3.5 3.5 0 0 1 19 6.5v5A3.5 3.5 0 0 1 15.5 15H11l-4.5 4v-4.2A3.5 3.5 0 0 1 5 11.5z" />
          <path d="M9 9h.01M12 9h.01M15 9h.01" />
        </svg>
      </button>

      {isOpen ? (
        <aside
          id="rag-chatbot-drawer"
          className="chatbot-drawer open"
          aria-label="RAG 챗봇 목업"
        >
          <header className="chatbot-header">
            <div>
              <p className="eyebrow">RAG Chat</p>
              <h2>레포지토리 질문</h2>
            </div>
            <div className="chatbot-header-actions">
              <button
                type="button"
                className="chatbot-new-session"
                onClick={createNewSession}
              >
                새 대화
              </button>
              <button
                type="button"
                className="chatbot-close"
                onClick={closeDrawer}
                aria-label="챗봇 닫기"
              >
                닫기
              </button>
            </div>
          </header>

          <section className="chatbot-context" aria-label="현재 질문 기준">
            <div className="chatbot-context-main">
              <div>
                <strong>
                  {chatContext.title}
                </strong>
                <span>{chatContext.detail}</span>
                {chatContext.technicalDetail ? (
                  <span>{chatContext.technicalDetail}</span>
                ) : null}
              </div>
              <span className="chatbot-dev-badge">LLM 미연결</span>
            </div>
            {chatContext.warning ? (
              <p className="chatbot-context-warning">{chatContext.warning}</p>
            ) : null}
            <div className="chatbot-basis-summary">
              <div className="chatbot-basis-chips" aria-label="선택된 답변 기준">
                {chatContext.selectedRuns.length ? (
                  <>
                    {chatContext.selectedRuns.slice(0, 2).map((run) => (
                      <span className="chatbot-basis-chip" key={run.id}>
                        {formatRunChipLabel(run)}
                      </span>
                    ))}
                    {chatContext.selectedRuns.length > 2 ? (
                      <span className="chatbot-basis-chip">
                        +{chatContext.selectedRuns.length - 2}
                      </span>
                    ) : null}
                  </>
                ) : (
                  <span className="chatbot-basis-chip">대화로 선택</span>
                )}
              </div>
              <button
                type="button"
                onClick={toggleBasisPicker}
              >
                {isBasisPickerOpen ? '닫기' : '기준 변경'}
              </button>
            </div>
            {isBasisPickerOpen ? (
              <fieldset className="chatbot-basis-picker">
                <legend>답변 기준 선택</legend>
                <label>
                  <input
                    type="checkbox"
                    checked={selectedRunIds.length === 0}
                    onChange={selectConversationBasis}
                  />
                  <span>대화로 선택</span>
                </label>
                {chatBasisOptions.map((run) => (
                  <label key={run.id}>
                    <input
                      type="checkbox"
                      checked={selectedRunIds.includes(run.id)}
                      onChange={() => toggleSelectedRun(run.id)}
                    />
                    <span>{formatRunOptionLabel(run)}</span>
                  </label>
                ))}
              </fieldset>
            ) : null}
          </section>

          <div className={`chatbot-body ${hasMultipleSessions ? '' : 'single-session'}`}>
            {hasMultipleSessions ? (
              <nav className="chatbot-session-panel" aria-label="챗봇 대화 세션">
                <ul className="chatbot-session-list">
                  {sessions.map((session) => (
                    <li key={session.id}>
                      <div className="chatbot-session-item">
                        <button
                          type="button"
                          className={session.id === activeSession.id ? 'active' : ''}
                          onClick={() => {
                            setActiveSessionId(session.id)
                            setDraft('')
                            setDraftError('')
                          }}
                        >
                          <strong>{session.title}</strong>
                          <span>{formatSessionTime(session.updatedAt)}</span>
                        </button>
                        <button
                          type="button"
                          className="chatbot-session-delete"
                          onClick={() => deleteSession(session.id)}
                          aria-label={`${session.title} 채팅방 삭제`}
                        >
                          <span aria-hidden="true" />
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              </nav>
            ) : null}

            <div className="chatbot-messages" aria-live="polite">
              {messages.map((message) => (
                <article
                  key={message.id}
                  className={`chatbot-message ${message.sender}`}
                >
                  <span>{getMessageSenderLabel(message.sender)}</span>
                  <p>{message.text}</p>
                </article>
              ))}

              {activeSession.isGenerating ? (
                <div className="chatbot-loading" role="status">
                  <span>답변 생성 중</span>
                  <div className="chatbot-loading-track" aria-hidden="true">
                    <i />
                  </div>
                </div>
              ) : null}
              <span ref={messagesEndRef} aria-hidden="true" />
            </div>
          </div>

          <form className="chatbot-form" onSubmit={submitMockMessage}>
            <label htmlFor="chatbot-question">질문</label>
            <textarea
              id="chatbot-question"
              value={draft}
              onChange={(event) => {
                setDraft(event.target.value)
                if (draftError) {
                  setDraftError('')
                }
              }}
              onKeyDown={submitOnEnter}
              placeholder={chatContext.hasSelectedRuns
                ? '이 레포 기준으로 다음 구현 계획을 제안해줘'
                : '어떤 레포를 읽고 답변할지 물어보세요'}
              rows="4"
              disabled={isChatInputDisabled}
              aria-invalid={Boolean(draftError)}
              aria-describedby={draftError ? 'chatbot-question-error' : undefined}
            />
            {draftError ? (
              <p className="chatbot-form-error" id="chatbot-question-error">
                {draftError}
              </p>
            ) : null}
            <div className="chatbot-actions">
              <button
                type="submit"
                className="primary-action"
                disabled={isChatInputDisabled}
              >
                {activeSession.isGenerating ? '생성 중' : '보내기'}
              </button>
            </div>
          </form>
        </aside>
      ) : null}
    </>
  )
}

function createChatSession(id, title) {
  return {
    id,
    title,
    isGenerating: false,
    updatedAt: new Date().toISOString(),
    messages: [
      {
        id: `intro-${id}`,
        sender: 'assistant',
        text: '레포지토리 분석 결과를 기준으로 질문을 도와드릴게요. 지금은 화면 흐름을 확인하기 위한 목업입니다.',
      },
    ],
  }
}

function createRunIdsSignature(runIds) {
  return [...runIds].sort((left, right) => Number(left) - Number(right)).join('|')
}

function buildBasisChangedMessage(selectedRuns) {
  if (!selectedRuns.length) {
    return '답변 기준이 대화로 선택으로 변경됨'
  }

  const basisLabel = selectedRuns
    .map((run) => formatRunChipLabel(run))
    .join(', ')
  return `답변 기준이 ${basisLabel}으로 변경됨`
}

function getMessageSenderLabel(sender) {
  if (sender === 'user') {
    return '나'
  }

  if (sender === 'system') {
    return '기준'
  }

  return 'LLM'
}

function resolveSessionTitle(session, question) {
  if (session.title !== '새 대화') {
    return session.title
  }

  return question.length > 18 ? `${question.slice(0, 18)}...` : question
}

function formatSessionTime(value) {
  return new Intl.DateTimeFormat('ko-KR', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function buildChatContext(selectedRuns, isIndexing) {
  if (!selectedRuns.length) {
    return {
      title: '답변 기준: 대화로 선택',
      modeLabel: '대화로 선택',
      hasSelectedRuns: false,
      selectedRuns: [],
      detail: isIndexing
        ? '새 분석이 진행 중입니다. 질문은 가능하고, 완료되면 답변 기준이 자동으로 잡힙니다.'
        : '질문과 대화 맥락에서 필요한 레포를 찾습니다.',
      technicalDetail: '',
      warning: '',
    }
  }

  if (selectedRuns.length === 1) {
    const run = selectedRuns[0]

    return {
      title: '답변 기준: 마지막 완료 분석본',
      modeLabel: '선택한 레포',
      hasSelectedRuns: true,
      selectedRuns,
      detail: `${run.repository_full_name} · ${run.branch || '기본'}`,
      technicalDetail: formatRunDetailLabel(run),
      warning: isIndexing
        ? '새 분석이 진행 중입니다. 완료 전까지는 선택한 완료 답변 기준으로 답변합니다.'
        : '',
    }
  }

  return {
    title: `답변 기준: 마지막 완료 분석본 ${selectedRuns.length}개`,
    modeLabel: '여러 레포 선택',
    hasSelectedRuns: true,
    selectedRuns,
    detail: selectedRuns.map((run) => formatRunReferenceLabel(run)).join(', '),
    technicalDetail: '내부 검색은 각 분석본의 repository_full_name, branch, commit_sha로 고정됩니다.',
    warning: isIndexing
      ? '새 분석이 진행 중입니다. 완료 전까지는 선택한 완료 답변 기준으로 답변합니다.'
      : '',
  }
}

function buildMockAssistantText(chatContext) {
  if (!chatContext.hasSelectedRuns) {
    return '현재 고정된 답변 기준은 없습니다. 실제 연결 시에는 사용자의 질문과 대화 맥락에서 레포를 파악하고, 해당 레포의 가장 최신 완료 답변 기준으로 답변합니다.'
  }

  return `${chatContext.detail} 기준으로 답변이 생성될 예정입니다. 실제 연결 시 내부 검색은 repository_full_name, branch, commit_sha로 고정하고 선택된 RAG 근거와 대화 중 추가된 레포 맥락을 함께 사용합니다.`
}

function buildChatBasisOptions(repositoryRuns, indexResult) {
  const optionsById = new Map()

  for (const run of repositoryRuns || []) {
    if (run.id && run.repository_full_name) {
      optionsById.set(run.id, run)
    }
  }

  if (indexResult?.run_id && indexResult.repository_full_name) {
    optionsById.set(indexResult.run_id, {
      id: indexResult.run_id,
      repository_full_name: indexResult.repository_full_name,
      branch: indexResult.branch,
      commit_sha: indexResult.commit_sha || indexResult.pipeline_result?.commit_sha,
      indexed_at: indexResult.indexed_at,
    })
  }

  return Array.from(optionsById.values()).sort(
    (left, right) => new Date(right.indexed_at || 0) - new Date(left.indexed_at || 0),
  )
}

function formatRunOptionLabel(run) {
  return formatRunReferenceLabel(run)
}

function formatRunChipLabel(run) {
  return formatRunReferenceLabel(run)
}

function formatRunReferenceLabel(run) {
  const branch = run.branch || '기본'
  const indexedAt = formatIndexedAt(run.indexed_at)
  const analysis = indexedAt ? ` · 마지막 분석 ${indexedAt}` : ' · 마지막 분석 시각 없음'
  return `${run.repository_full_name} · ${branch}${analysis}`
}

function formatRunTechnicalLabel(run) {
  if (run.commit_sha) {
    return `코드 버전 ${run.commit_sha.slice(0, 7)}`
  }

  return `run #${run.id}`
}

function formatRunDetailLabel(run) {
  const indexedAt = formatIndexedAt(run.indexed_at)
  const analysis = indexedAt ? `분석 완료: ${indexedAt}` : '분석 완료 시각 없음'
  return `${analysis} · ${formatRunTechnicalLabel(run)}`
}

function formatIndexedAt(value) {
  if (!value) {
    return ''
  }

  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}
