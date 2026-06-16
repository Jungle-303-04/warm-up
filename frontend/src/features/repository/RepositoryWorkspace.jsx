export function RepositoryWorkspace({
  repositoryFullName,
  branch,
  indexResult,
  question,
  answerResult,
  repositoryRuns,
  isLoading,
  isIndexing,
  isAsking,
  isLoadingRepositoryRuns,
  onRepositoryChange,
  onBranchChange,
  onQuestionChange,
  onIndexRepository,
  onAskRepository,
  onReloadRepositoryRuns,
  onSelectRepositoryRun,
}) {
  return (
    <section className="workspace-panel" aria-labelledby="workspace-title">
      <h2 id="workspace-title">레포지토리 분석</h2>

      <RepositoryRunList
        repositoryRuns={repositoryRuns}
        isLoadingRepositoryRuns={isLoadingRepositoryRuns}
        onReload={onReloadRepositoryRuns}
        onSelectRepositoryRun={onSelectRepositoryRun}
      />

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
  // Backend: POST /rag/github/repository/index/store
  // Response DTO인 RagStoredIndexResponseDTO를 사용자용으로 줄여 보여준다.
  // 화면에는 내부 저장 개수(sql_chunk_count/vector_chunk_count)보다
  // repository_full_name, branch, indexed_at 중심으로 표시한다.
  const repositoryName = indexResult.repository_full_name || '-'
  const branch = indexResult.branch || '기본 브랜치'
  const indexedAt = indexResult.indexed_at

  return (
    <dl className="run-summary" aria-label="최근 분석 결과">
      <div>
        <dt>레포지토리</dt>
        <dd>{repositoryName}</dd>
      </div>
      <div>
        <dt>브랜치</dt>
        <dd>{branch}</dd>
      </div>
      <div>
        <dt>마지막 분석</dt>
        <dd>{formatDateTime(indexedAt)}</dd>
      </div>
    </dl>
  )
}

function RepositoryRunList({
  repositoryRuns,
  isLoadingRepositoryRuns,
  onReload,
  onSelectRepositoryRun,
}) {
  // Backend: GET /rag/runs
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
  // App.jsx에서 repository_full_name + branch 기준 최신 run만 추려 넘긴다.
  // 사용자가 항목을 누르면 repository_full_name, branch, commit_sha를 질문 기준으로 사용한다.
  return (
    <section className="repository-run-panel" aria-labelledby="repository-run-title">
      <div className="repository-run-header">
        <div>
          <p className="eyebrow">분석된 레포</p>
          <h3 id="repository-run-title">마지막 분석 시각</h3>
        </div>
        <button
          type="button"
          className="secondary-button compact"
          onClick={onReload}
          disabled={isLoadingRepositoryRuns}
        >
          {isLoadingRepositoryRuns ? '확인 중' : '새로고침'}
        </button>
      </div>

      {repositoryRuns.length ? (
        <ul className="repository-run-list">
          {repositoryRuns.map((run) => (
            <li key={`${run.repository_full_name}-${run.branch || ''}`}>
              <button type="button" onClick={() => onSelectRepositoryRun(run)}>
                <span>
                  <strong>{run.repository_full_name}</strong>
                  <small>{run.branch || '기본 브랜치'}</small>
                </span>
                <time dateTime={run.indexed_at}>{formatDateTime(run.indexed_at)}</time>
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <p className="repository-run-empty">
          아직 분석된 레포지토리가 없습니다.
        </p>
      )}
    </section>
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

function formatDateTime(value) {
  if (!value) {
    return '-'
  }

  return new Intl.DateTimeFormat('ko-KR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}
