import { useMemo, useState } from 'react'

const INITIAL_MESSAGES = [
  {
    id: 1,
    sender: 'assistant',
    text: '레포지토리 분석 결과를 기준으로 질문을 도와드릴게요. 지금은 화면 흐름을 확인하기 위한 목업입니다.',
  },
]

export function ChatbotDrawer({ repositoryFullName, branch, indexResult }) {
  const [isOpen, setIsOpen] = useState(false)
  const [draft, setDraft] = useState('')
  const [messages, setMessages] = useState(INITIAL_MESSAGES)

  const chatContext = useMemo(
    () => buildChatContext(repositoryFullName, branch, indexResult),
    [repositoryFullName, branch, indexResult],
  )

  function submitMockMessage(event) {
    event.preventDefault()

    const nextQuestion = draft.trim()
    if (!nextQuestion) {
      return
    }

    // Future backend connection:
    // POST /rag/ask 또는 별도 chatbot endpoint로 연결한다.
    // Expected request DTO:
    // {
    //   question: string,
    //   repository_full_name: string,
    //   branch?: string | null,
    //   commit_sha?: string | null,
    //   limit: number
    // }
    // Current implementation is a frontend mock, so it does not send an API request yet.
    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text: nextQuestion,
    }
    const assistantMessage = {
      id: Date.now() + 1,
      sender: 'assistant',
      text: chatContext.repositoryName
        ? `${chatContext.repositoryName} 기준으로 답변이 생성될 예정입니다. 실제 연결 시 저장된 RAG 근거와 함께 LLM으로 전달됩니다.`
        : '먼저 레포지토리를 분석하거나 분석된 레포를 선택하면, 그 결과를 기준으로 답변이 생성될 예정입니다.',
    }

    setMessages((currentMessages) => [
      ...currentMessages,
      userMessage,
      assistantMessage,
    ])
    setDraft('')
  }

  function clearMessages() {
    setMessages(INITIAL_MESSAGES)
  }

  return (
    <>
      <button
        type="button"
        className="chatbot-launcher"
        onClick={() => setIsOpen(true)}
        aria-label="챗봇 열기"
      >
        챗봇
      </button>

      <aside
        className={`chatbot-drawer${isOpen ? ' open' : ''}`}
        aria-label="RAG 챗봇 목업"
        aria-hidden={!isOpen}
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
        </section>

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
        </div>

        <form className="chatbot-form" onSubmit={submitMockMessage}>
          <label htmlFor="chatbot-question">질문</label>
          <textarea
            id="chatbot-question"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="이 레포 기준으로 다음 구현 계획을 제안해줘"
            rows="4"
          />
          <div className="chatbot-actions">
            <button
              type="button"
              className="secondary-button compact"
              onClick={clearMessages}
            >
              비우기
            </button>
            <button type="submit" className="primary-action">
              보내기
            </button>
          </div>
        </form>
      </aside>
    </>
  )
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
