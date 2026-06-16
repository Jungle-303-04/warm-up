import { useEffect, useMemo, useRef, useState } from 'react'

const INITIAL_SESSION_ID = 1
const MOCK_RESPONSE_DELAY_MS = 900

export function ChatbotDrawer({ repositoryFullName, branch, indexResult }) {
  const responseTimerIds = useRef(new Map())
  const sessionIdRef = useRef(INITIAL_SESSION_ID + 1)
  const messageIdRef = useRef(100)
  const [isOpen, setIsOpen] = useState(false)
  const [draft, setDraft] = useState('')
  const [activeSessionId, setActiveSessionId] = useState(INITIAL_SESSION_ID)
  const [sessions, setSessions] = useState(() => [
    createChatSession(INITIAL_SESSION_ID, '새 대화'),
  ])

  const chatContext = useMemo(
    () => buildChatContext(repositoryFullName, branch, indexResult),
    [repositoryFullName, branch, indexResult],
  )
  const activeSession = sessions.find((session) => session.id === activeSessionId)
    || sessions[0]
  const messages = activeSession?.messages || []

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

  function createNewSession() {
    const nextSession = createChatSession(sessionIdRef.current, '새 대화')
    sessionIdRef.current += 1
    setSessions((currentSessions) => [nextSession, ...currentSessions])
    setActiveSessionId(nextSession.id)
    setDraft('')
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
      return
    }

    const nextSessions = sessions.filter((session) => session.id !== sessionId)
    setSessions(nextSessions)

    if (sessionId === activeSessionId) {
      setActiveSessionId(nextSessions[0].id)
      setDraft('')
    }
  }

  function submitMockMessage(event) {
    event.preventDefault()
    sendMockMessage()
  }

  function sendMockMessage() {
    const nextQuestion = draft.trim()
    if (!nextQuestion || activeSession.isGenerating) {
      return
    }

    // Future backend connection:
    // POST /rag/ask 또는 별도 chatbot session endpoint로 연결한다.
    // Expected request DTO per session:
    // {
    //   session_id: number | string,
    //   question: string,
    //   repository_full_name: string,
    //   branch?: string | null,
    //   commit_sha?: string | null,
    //   limit: number
    // }
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
      text: chatContext.repositoryName
        ? `${chatContext.repositoryName} 기준으로 답변이 생성될 예정입니다. 실제 연결 시 저장된 RAG 근거와 함께 LLM으로 전달됩니다.`
        : '먼저 레포지토리를 분석하거나 분석된 레포를 선택하면, 그 결과를 기준으로 답변이 생성될 예정입니다.',
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
        onClick={() => setIsOpen(true)}
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
            <button
              type="button"
              className="chatbot-close"
              onClick={() => setIsOpen(false)}
              aria-label="챗봇 닫기"
            >
              닫기
            </button>
          </header>

          <section className="chatbot-context" aria-label="현재 질문 기준">
            <strong>{chatContext.repositoryName || '분석 기준 없음'}</strong>
            <span>{chatContext.detail}</span>
            <dl className="chatbot-readiness">
              <div>
                <dt>분석 기준</dt>
                <dd>{chatContext.repositoryName ? '선택됨' : '필요함'}</dd>
              </div>
              <div>
                <dt>답변 상태</dt>
                <dd>목업 응답</dd>
              </div>
            </dl>
            <p>
              아직 실제 LLM API와 연결되지 않았습니다. 현재 대화는 화면 흐름을 확인하기 위한
              목업 응답입니다.
            </p>
          </section>

          <div className="chatbot-body">
            <nav className="chatbot-session-panel" aria-label="챗봇 대화 세션">
              <button
                type="button"
                className="secondary-button compact"
                onClick={createNewSession}
              >
                새 대화
              </button>
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

            <div className="chatbot-messages" aria-live="polite">
              {messages.map((message) => (
                <article
                  key={message.id}
                  className={`chatbot-message ${message.sender}`}
                >
                  <span>{message.sender === 'user' ? '나' : 'LLM'}</span>
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
            </div>
          </div>

          <form className="chatbot-form" onSubmit={submitMockMessage}>
            <label htmlFor="chatbot-question">질문</label>
            <textarea
              id="chatbot-question"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={submitOnEnter}
              placeholder="이 레포 기준으로 다음 구현 계획을 제안해줘"
              rows="4"
              disabled={activeSession.isGenerating}
            />
            <div className="chatbot-actions">
              <button
                type="submit"
                className="primary-action"
                disabled={activeSession.isGenerating}
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

function buildChatContext(repositoryFullName, branch, indexResult) {
  const repositoryName = indexResult?.repository_full_name || repositoryFullName.trim()
  const branchName = indexResult?.branch || branch.trim()
  const commitSha = indexResult?.commit_sha || indexResult?.pipeline_result?.commit_sha

  if (!repositoryName) {
    return {
      repositoryName: '',
      detail: '레포지토리 분석 후 질문 기준이 자동으로 잡힙니다.',
    }
  }

  const parts = [branchName || '기본 브랜치']
  if (commitSha) {
    parts.push(`commit ${commitSha.slice(0, 7)}`)
  }

  return {
    repositoryName,
    detail: parts.join(' · '),
  }
}
