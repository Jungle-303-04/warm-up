import { useEffect, useMemo, useRef, useState } from 'react'

import { API_BASE_URL } from '../../app/config'
import { postJson, toKoreanErrorMessage } from '../../shared/api/http'

const INITIAL_SESSION_ID = 1

export function ChatbotDrawer({
  indexResult,
  isIndexing,
  repositoryRuns,
  selectedRunIds = [],
  onSelectedRunIdsChange = () => undefined,
}) {
  const draftInputRef = useRef(null)
  const draftFocusTimeoutRef = useRef(null)
  const messagesEndRef = useRef(null)
  const selectedRunIdsSignatureRef = useRef(createRunIdsSignature(selectedRunIds))
  const shouldRestoreDraftFocusRef = useRef(false)
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
  const [agentBasisRuns, setAgentBasisRuns] = useState([])
  const chatBasisOptions = useMemo(
    () => buildChatBasisOptions(repositoryRuns, indexResult),
    [repositoryRuns, indexResult],
  )
  const selectedRuns = useMemo(
    () => chatBasisOptions.filter((run) => selectedRunIds.includes(run.id)),
    [chatBasisOptions, selectedRunIds],
  )
  const effectiveSelectedRuns = selectedRuns.length ? selectedRuns : agentBasisRuns
  const isAgentInferredBasis = !selectedRuns.length && agentBasisRuns.length > 0

  const chatContext = useMemo(
    () => buildChatContext(effectiveSelectedRuns, isIndexing, isAgentInferredBasis),
    [effectiveSelectedRuns, isIndexing, isAgentInferredBasis],
  )
  const activeSession = sessions.find((session) => session.id === activeSessionId)
    || sessions[0]
  const messages = activeSession?.messages || []
  const isChatInputDisabled = Boolean(activeSession?.isGenerating)
  const hasMultipleSessions = sessions.length > 1

  function requestDraftFocus() {
    shouldRestoreDraftFocusRef.current = true
    window.requestAnimationFrame(() => {
      restoreDraftFocusIfReady()
      window.clearTimeout(draftFocusTimeoutRef.current)
      draftFocusTimeoutRef.current = window.setTimeout(restoreDraftFocusIfReady, 50)
    })
  }

  function restoreDraftFocusIfReady() {
    const input = draftInputRef.current
    if (!input || input.disabled) {
      return
    }

    shouldRestoreDraftFocusRef.current = false
    input.focus({ preventScroll: true })
  }

  useEffect(() => {
    document.body.classList.toggle('chatbot-drawer-open', isOpen)

    return () => {
      document.body.classList.remove('chatbot-drawer-open')
    }
  }, [isOpen])

  useEffect(() => () => {
    window.clearTimeout(draftFocusTimeoutRef.current)
  }, [])

  useEffect(() => {
    if (!isOpen) {
      return
    }

    messagesEndRef.current?.scrollIntoView({ block: 'end' })
  }, [activeSessionId, messages.length, activeSession?.isGenerating, isOpen])

  useEffect(() => {
    if (!isOpen || isChatInputDisabled || !shouldRestoreDraftFocusRef.current) {
      return undefined
    }

    const frameId = window.requestAnimationFrame(restoreDraftFocusIfReady)
    return () => window.cancelAnimationFrame(frameId)
  }, [isOpen, isChatInputDisabled, activeSessionId, messages.length])

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
    requestDraftFocus()
  }

  function openDrawer() {
    setIsOpen(true)
    setDraftError('')
    shouldRestoreDraftFocusRef.current = true
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
    setAgentBasisRuns([])
    setDraftError('')
  }

  function deleteSession(sessionId) {
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

  function submitChatMessage(event) {
    event.preventDefault()
    void sendChatMessage()
  }

  function toggleSelectedRun(runId) {
    setAgentBasisRuns([])
    onSelectedRunIdsChange(
      selectedRunIds.includes(runId)
        ? selectedRunIds.filter((currentRunId) => currentRunId !== runId)
        : [...selectedRunIds, runId],
    )
    setDraftError('')
  }

  async function sendChatMessage() {
    const nextQuestion = draft.trim()
    if (!nextQuestion) {
      setDraftError('질문을 입력한 뒤 보내기를 눌러 주세요.')
      requestDraftFocus()
      return
    }

    if (isChatInputDisabled) {
      return
    }

    const userMessage = {
      id: messageIdRef.current,
      sender: 'user',
      text: nextQuestion,
    }
    messageIdRef.current += 1
    const sessionId = activeSession.id
    const nextTitle = resolveSessionTitle(activeSession, nextQuestion)
    const requestRepositoryRefs = effectiveSelectedRuns.map(buildAgentRepositoryRef)
    let agentSessionId

    try {
      agentSessionId = await ensureAgentSession(sessionId, nextTitle)
    } catch (error) {
      setDraftError(toKoreanErrorMessage(error.message))
      requestDraftFocus()
      return
    }

    shouldRestoreDraftFocusRef.current = true
    setSessions((currentSessions) =>
      currentSessions.map((session) => {
        if (session.id !== sessionId) {
          return session
        }

        return {
          ...session,
          isGenerating: true,
          title: nextTitle,
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

    try {
      const response = await sendAgentChatMessageWithRecovery(
        sessionId,
        agentSessionId,
        nextTitle,
        nextQuestion,
        requestRepositoryRefs,
      )
      if (response.repository_basis_changed) {
        const nextBasisRuns = buildRunsFromAgentRefs(
          response.inferred_repository_refs || [],
          chatBasisOptions,
        )
        setAgentBasisRuns(nextBasisRuns)

        const inferredRunIds = nextBasisRuns
          .map((run) => run.id)
          .filter((runId) => typeof runId === 'number')
        onSelectedRunIdsChange(inferredRunIds)
      }

      replaceSessionWithAgentResponse(sessionId, response, nextTitle)
    } catch (error) {
      appendAssistantMessage(sessionId, toKoreanErrorMessage(error.message))
    }
  }

  async function sendAgentChatMessageWithRecovery(
    sessionId,
    agentSessionId,
    title,
    question,
    repositoryRefs,
  ) {
    try {
      return await sendAgentChatMessage(agentSessionId, question, repositoryRefs)
    } catch (error) {
      if (!isChatSessionNotFoundError(error)) {
        throw error
      }

      // 개발 서버 reload 후에는 백엔드 InMemoryChatStore의 세션만 사라질 수 있다.
      // 로컬 대화 UI는 유지하되, 새 백엔드 세션을 같은 채팅방에 다시 연결해 재전송한다.
      const recoveredAgentSessionId = await recreateAgentSession(sessionId, title)
      return sendAgentChatMessage(recoveredAgentSessionId, question, repositoryRefs)
    }
  }

  async function recreateAgentSession(sessionId, title) {
    const response = await createAgentChatSession(title)
    const agentSessionId = response.session.id

    setSessions((currentSessions) =>
      currentSessions.map((session) => (
        session.id === sessionId
          ? {
            ...session,
            agentSessionId,
            title: session.title === '새 대화' ? title : session.title,
          }
          : session
      )),
    )
    return agentSessionId
  }

  async function ensureAgentSession(sessionId, title) {
    const currentSession = sessions.find((session) => session.id === sessionId)
    if (currentSession?.agentSessionId) {
      return currentSession.agentSessionId
    }

    const response = await createAgentChatSession(title)
    const agentSessionId = response.session.id
    setSessions((currentSessions) =>
      currentSessions.map((session) => (
        session.id === sessionId
          ? {
            ...session,
            agentSessionId,
            title: session.title === '새 대화' ? title : session.title,
          }
          : session
      )),
    )
    return agentSessionId
  }

  function submitOnEnter(event) {
    if (event.key !== 'Enter' || event.shiftKey) {
      return
    }

    if (isChatInputDisabled) {
      return
    }

    event.preventDefault()
    void sendChatMessage()
  }

  function appendAssistantMessage(sessionId, text) {
    const assistantMessage = {
      id: messageIdRef.current,
      sender: 'assistant',
      text,
    }
    messageIdRef.current += 1

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
    requestDraftFocus()
  }

  function replaceSessionWithAgentResponse(sessionId, response, title) {
    const responseMessages = (response.messages || []).map(toLocalChatMessage)
    setSessions((currentSessions) =>
      currentSessions.map((session) => {
        if (session.id !== sessionId) {
          return session
        }

        return {
          ...session,
          agentSessionId: response.session.id,
          title,
          isGenerating: false,
          updatedAt: new Date().toISOString(),
          messages: responseMessages,
        }
      }),
    )
    requestDraftFocus()
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
          aria-label="레포지토리 질문 도우미"
        >
          <header className="chatbot-header">
            <div>
              <p className="eyebrow">AI 질문</p>
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

          <section className="chatbot-context" aria-label="현재 답변 대상">
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
              <span className="chatbot-dev-badge">실제 답변</span>
            </div>
            {chatContext.warning ? (
              <p className="chatbot-context-warning">{chatContext.warning}</p>
            ) : null}
            <div className="chatbot-basis-summary">
              <div className="chatbot-basis-chips" aria-label="선택된 답변 대상">
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
                  <span className="chatbot-basis-chip">질문에서 찾기</span>
                )}
              </div>
              <button
                type="button"
                onClick={toggleBasisPicker}
              >
                {isBasisPickerOpen ? '닫기' : '대상 변경'}
              </button>
            </div>
            {isBasisPickerOpen ? (
              <fieldset className="chatbot-basis-picker">
                <legend>답변에 사용할 레포지토리</legend>
                <label>
                  <input
                    type="checkbox"
                    checked={selectedRunIds.length === 0}
                    onChange={selectConversationBasis}
                  />
                  <span>질문에서 자동으로 찾기</span>
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
                            requestDraftFocus()
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

              {activeSession?.isGenerating ? (
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

          <form className="chatbot-form" onSubmit={submitChatMessage}>
            <label htmlFor="chatbot-question">질문</label>
            <textarea
              ref={draftInputRef}
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
                ? '이 레포지토리로 다음 구현 계획을 제안해줘'
                : '레포지토리 이름이나 브랜치를 포함해서 질문해 보세요'}
              rows="4"
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
                {activeSession?.isGenerating ? '생성 중' : '보내기'}
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
    agentSessionId: null,
    title,
    isGenerating: false,
    updatedAt: new Date().toISOString(),
    messages: [
      {
        id: `intro-${id}`,
        sender: 'assistant',
        text: '분석된 레포지토리를 기준으로 답변합니다. 위에서 레포지토리를 고르거나 질문에 레포 이름과 브랜치를 써 주세요.',
      },
    ],
  }
}

async function createAgentChatSession(title) {
  return postJson(`${API_BASE_URL}/agent/chat/sessions`, { title })
}

async function sendAgentChatMessage(sessionId, content, repositoryRefs) {
  return postJson(`${API_BASE_URL}/agent/chat/sessions/${sessionId}/messages`, {
    content,
    repository_refs: repositoryRefs,
  })
}

function isChatSessionNotFoundError(error) {
  return String(error?.message || '').includes('chat session not found')
}

function buildAgentRepositoryRef(run) {
  return {
    run_id: Number.isInteger(run.id) ? run.id : null,
    repository_full_name: run.repository_full_name,
    branch: run.branch || null,
    commit_sha: run.commit_sha || null,
  }
}

function toLocalChatMessage(message) {
  return {
    id: message.id,
    sender: toLocalMessageSender(message.role),
    text: message.content,
  }
}

function toLocalMessageSender(role) {
  if (role === 'user') {
    return 'user'
  }

  if (role === 'assistant') {
    return 'assistant'
  }

  return 'system'
}

function buildRunsFromAgentRefs(refs, chatBasisOptions) {
  return refs
    .map((ref) => findRunForAgentRef(ref, chatBasisOptions))
    .filter(Boolean)
}

function findRunForAgentRef(ref, chatBasisOptions) {
  const runId = ref.run_id
  const matchedByRunId = runId
    ? chatBasisOptions.find((run) => run.id === runId)
    : null
  if (matchedByRunId) {
    return matchedByRunId
  }

  const matchedByRepositoryRef = chatBasisOptions.find((run) => (
    run.repository_full_name === ref.repository_full_name
    && normalizeOptionalText(run.branch) === normalizeOptionalText(ref.branch)
    && normalizeOptionalText(run.commit_sha) === normalizeOptionalText(ref.commit_sha)
  ))
  if (matchedByRepositoryRef) {
    return matchedByRepositoryRef
  }

  if (!ref.repository_full_name) {
    return null
  }

  return {
    id: runId || `${ref.repository_full_name}:${ref.branch || ''}:${ref.commit_sha || ''}`,
    repository_full_name: ref.repository_full_name,
    branch: ref.branch,
    commit_sha: ref.commit_sha,
    indexed_at: '',
  }
}

function normalizeOptionalText(value) {
  return String(value || '').trim()
}

function createRunIdsSignature(runIds) {
  return [...runIds].sort((left, right) => Number(left) - Number(right)).join('|')
}

function buildBasisChangedMessage(selectedRuns) {
  if (!selectedRuns.length) {
    return '앞으로 질문 내용에서 답변할 레포지토리를 찾습니다.'
  }

  const basisLabel = selectedRuns
    .map((run) => formatRunChipLabel(run))
    .join(', ')
  return `앞으로 ${basisLabel} 분석 결과로 답변합니다.`
}

function getMessageSenderLabel(sender) {
  if (sender === 'user') {
    return '나'
  }

  if (sender === 'system') {
    return '안내'
  }

  return 'AI'
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

function buildChatContext(selectedRuns, isIndexing, isAgentInferredBasis = false) {
  if (!selectedRuns.length) {
    return {
      title: '답변 대상: 질문에서 찾기',
      modeLabel: '질문에서 찾기',
      hasSelectedRuns: false,
      selectedRuns: [],
      detail: isIndexing
        ? '새 분석이 진행 중입니다. 질문은 가능하고, 완료되면 새 분석 결과를 선택할 수 있습니다.'
        : '질문에 적힌 레포지토리 이름이나 브랜치를 보고 답변 대상을 찾습니다.',
      technicalDetail: '',
      warning: '',
    }
  }

  if (selectedRuns.length === 1) {
    const run = selectedRuns[0]

    return {
      title: isAgentInferredBasis
        ? '답변 대상: agent가 찾은 분석 결과'
        : '답변 대상: 선택한 분석 결과',
      modeLabel: isAgentInferredBasis ? 'agent 추론' : '선택한 레포',
      hasSelectedRuns: true,
      selectedRuns,
      detail: `${run.repository_full_name} · ${run.branch || '기본 브랜치'}`,
      technicalDetail: formatRunDetailLabel(run),
      warning: isIndexing
        ? '새 분석 중입니다. 완료되기 전까지는 지금 선택된 마지막 분석 결과로 답변합니다.'
        : '',
    }
  }

  return {
    title: isAgentInferredBasis
      ? `답변 대상: agent가 찾은 분석 결과 ${selectedRuns.length}개`
      : `답변 대상: 선택한 분석 결과 ${selectedRuns.length}개`,
    modeLabel: isAgentInferredBasis ? 'agent 추론' : '여러 레포 선택',
    hasSelectedRuns: true,
    selectedRuns,
    detail: selectedRuns.map((run) => formatRunReferenceLabel(run)).join(', '),
    technicalDetail: '선택된 각 레포지토리의 저장된 코드 버전을 기준으로 검색합니다.',
    warning: isIndexing
      ? '새 분석 중입니다. 완료되기 전까지는 지금 선택된 마지막 분석 결과로 답변합니다.'
      : '',
  }
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
  const branch = run.branch || '기본 브랜치'
  const indexedAt = formatIndexedAt(run.indexed_at)
  const analysis = indexedAt ? ` · 마지막 분석 ${indexedAt}` : ' · 마지막 분석 시각 없음'
  return `${run.repository_full_name} · ${branch}${analysis}`
}

function formatRunTechnicalLabel(run) {
  if (run.commit_sha) {
    return `코드 버전 ${run.commit_sha.slice(0, 7)}`
  }

  return '코드 버전 확인 전'
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
