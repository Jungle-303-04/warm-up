import { useMemo, useState } from 'react'

export function RepositoryWorkspace({
  repositoryFullName,
  branch,
  indexResult,
  repositoryRuns,
  isLoading,
  isIndexing,
  isLoadingRepositoryRuns,
  onRepositoryChange,
  onBranchChange,
  onIndexRepository,
  onReloadRepositoryRuns,
  onSelectRepositoryRun,
}) {
  const [isRunModalOpen, setIsRunModalOpen] = useState(false)
  const latestRun = repositoryRuns[0] || null

  function selectRun(run) {
    onSelectRepositoryRun(run)
    setIsRunModalOpen(false)
  }

  return (
    <section className="workspace-panel" aria-labelledby="workspace-title">
      <div className="workspace-header">
        <div>
          <p className="eyebrow">RAG index</p>
          <h2 id="workspace-title">레포지토리 분석</h2>
        </div>
        <span>{repositoryRuns.length}개 분석됨</span>
      </div>

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

      <RepositoryRunPreview
        latestRun={latestRun}
        repositoryCount={repositoryRuns.length}
        isLoadingRepositoryRuns={isLoadingRepositoryRuns}
        onReload={onReloadRepositoryRuns}
        onOpenAll={() => setIsRunModalOpen(true)}
      />

      {isRunModalOpen ? (
        <RepositoryRunModal
          repositoryRuns={repositoryRuns}
          isLoadingRepositoryRuns={isLoadingRepositoryRuns}
          onClose={() => setIsRunModalOpen(false)}
          onReload={onReloadRepositoryRuns}
          onSelectRepositoryRun={selectRun}
        />
      ) : null}
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

function RepositoryRunPreview({
  latestRun,
  repositoryCount,
  isLoadingRepositoryRuns,
  onReload,
  onOpenAll,
}) {
  // App.jsx가 Backend GET /rag/runs 응답을 repository_full_name + branch 기준으로
  // 최신 1개씩 정리해서 넘긴다. 여기서는 그중 가장 최근 항목 1개만 보여주고,
  // 전체 목록은 RepositoryRunModal에서 같은 DTO 데이터를 사용한다.
  return (
    <section className="repository-run-preview" aria-labelledby="repository-run-preview-title">
      <div>
        <p className="eyebrow">분석된 레포</p>
        <h3 id="repository-run-preview-title">최근 분석</h3>
      </div>

      {latestRun ? (
        <div className="repository-run-latest">
          <strong>{latestRun.repository_full_name}</strong>
          <span>
            {latestRun.branch || '기본 브랜치'} · {formatDateTime(latestRun.indexed_at)}
          </span>
        </div>
      ) : (
        <p className="repository-run-empty">아직 분석된 레포지토리가 없습니다.</p>
      )}

      <div className="repository-run-actions">
        <button
          type="button"
          className="secondary-button compact"
          onClick={onOpenAll}
          disabled={!repositoryCount}
        >
          전체 보기
        </button>
        <button
          type="button"
          className="secondary-button compact"
          onClick={onReload}
          disabled={isLoadingRepositoryRuns}
        >
          {isLoadingRepositoryRuns ? '확인 중' : '새로고침'}
        </button>
      </div>
    </section>
  )
}

function RepositoryRunModal({
  repositoryRuns,
  isLoadingRepositoryRuns,
  onReload,
  onClose,
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
  const sortedRuns = useMemo(
    () => [...repositoryRuns].sort(
      (left, right) => new Date(right.indexed_at) - new Date(left.indexed_at),
    ),
    [repositoryRuns],
  )

  return (
    <div className="repository-modal-backdrop" role="presentation">
      <section
        className="repository-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="repository-modal-title"
      >
        <header className="repository-modal-header">
          <div>
            <p className="eyebrow">분석된 레포</p>
            <h3 id="repository-modal-title">레포지토리 전체 보기</h3>
          </div>
          <button
            type="button"
            className="repository-modal-close"
            onClick={onClose}
            aria-label="레포지토리 목록 닫기"
          >
            닫기
          </button>
        </header>

        <div className="repository-modal-toolbar">
          <span>{repositoryRuns.length}개</span>
          <button
            type="button"
            className="secondary-button compact"
            onClick={onReload}
            disabled={isLoadingRepositoryRuns}
          >
            {isLoadingRepositoryRuns ? '확인 중' : '새로고침'}
          </button>
        </div>

        {sortedRuns.length ? (
          <ul className="repository-run-list">
            {sortedRuns.map((run) => (
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
    </div>
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
