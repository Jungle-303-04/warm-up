export function RepositoryWorkspace({
  repositoryFullName,
  branch,
  indexResult,
  question,
  answerResult,
  isLoading,
  isIndexing,
  isAsking,
  onRepositoryChange,
  onBranchChange,
  onQuestionChange,
  onIndexRepository,
  onAskRepository,
}) {
  return (
    <section className="workspace-panel" aria-labelledby="workspace-title">
      <h2 id="workspace-title">레포지토리 분석</h2>

      <RepositoryIndexForm
        repositoryFullName={repositoryFullName}
        branch={branch}
        isLoading={isLoading}
        isIndexing={isIndexing}
        onRepositoryChange={onRepositoryChange}
        onBranchChange={onBranchChange}
        onSubmit={onIndexRepository}
      />

      {indexResult ? <RunSummary indexResult={indexResult} /> : null}

      <RepositoryQuestionForm
        question={question}
        indexResult={indexResult}
        isLoading={isLoading}
        isAsking={isAsking}
        onQuestionChange={onQuestionChange}
        onSubmit={onAskRepository}
      />

      {answerResult ? <AnswerPanel answerResult={answerResult} /> : null}
    </section>
  )
}

function RepositoryIndexForm({
  repositoryFullName,
  branch,
  isLoading,
  isIndexing,
  onRepositoryChange,
  onBranchChange,
  onSubmit,
}) {
  return (
    <form className="workspace-form" onSubmit={onSubmit}>
      <label>
        <span>레포지토리</span>
        <input
          type="text"
          value={repositoryFullName}
          onChange={(event) => onRepositoryChange(event.target.value)}
          placeholder="owner/repo 또는 GitHub URL"
          autoComplete="off"
          disabled={isLoading}
        />
      </label>

      <label>
        <span>브랜치</span>
        <input
          type="text"
          value={branch}
          onChange={(event) => onBranchChange(event.target.value)}
          placeholder="비워두면 기본 브랜치 전체 분석"
          autoComplete="off"
          disabled={isLoading}
        />
      </label>

      <button type="submit" className="primary-action" disabled={isLoading}>
        {isIndexing ? '분석 중' : '분석 시작'}
      </button>

      {isIndexing ? (
        <ProgressPanel message="레포지토리 전체 파일을 검사하고 있습니다." />
      ) : null}
    </form>
  )
}

function RepositoryQuestionForm({
  question,
  indexResult,
  isLoading,
  isAsking,
  onQuestionChange,
  onSubmit,
}) {
  return (
    <form className="workspace-form" onSubmit={onSubmit}>
      <label>
        <span>질문</span>
        <textarea
          value={question}
          onChange={(event) => onQuestionChange(event.target.value)}
          placeholder="이 레포 기준으로 다음 구현 계획을 제안해줘"
          rows="4"
          disabled={isLoading}
        />
      </label>

      <button
        type="submit"
        className="primary-action"
        disabled={isLoading || !indexResult}
      >
        {isAsking ? '답변 생성 중' : 'LLM 액션 실행'}
      </button>

      {isAsking ? (
        <ProgressPanel message="저장된 RAG 근거를 찾고 LLM 답변을 생성하고 있습니다." />
      ) : null}
    </form>
  )
}

function ProgressPanel({ message }) {
  return (
    <div className="progress-panel" role="status" aria-live="polite">
      <div className="progress-header">
        <span>{message}</span>
        <strong>진행 중</strong>
      </div>
      <div className="progress-track" role="progressbar">
        <span />
      </div>
    </div>
  )
}

function RunSummary({ indexResult }) {
  return (
    <dl className="run-summary">
      <div>
        <dt>Run</dt>
        <dd>{indexResult.run_id}</dd>
      </div>
      <div>
        <dt>SQL</dt>
        <dd>{indexResult.sql_chunk_count}</dd>
      </div>
      <div>
        <dt>Vector</dt>
        <dd>{indexResult.vector_chunk_count}</dd>
      </div>
    </dl>
  )
}

function AnswerPanel({ answerResult }) {
  return (
    <section className="answer-panel" aria-label="LLM 답변">
      <p>{answerResult.answer}</p>
      <ul>
        {answerResult.sources.map((source) => (
          <li key={`${source.citation}-${source.distance}`}>
            {source.citation}
          </li>
        ))}
      </ul>
    </section>
  )
}
