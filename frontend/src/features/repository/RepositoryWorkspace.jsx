import { useMemo, useState } from 'react'

const REPOSITORY_RUNS_PAGE_SIZE = 10

export function RepositoryWorkspace({
  repositoryFullName,
  branch,
  indexResult,
  isLoading,
  isIndexing,
  onRepositoryChange,
  onBranchChange,
  onIndexRepository,
}) {
  return (
    <section className="workspace-panel" aria-labelledby="workspace-title">
      <div className="workspace-header">
        <div>
          <p className="eyebrow">RAG index</p>
          <h2 id="workspace-title">레포지토리 등록</h2>
        </div>
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
    </section>
  )
}

export function RepositoryRunsPage({
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
  const [pageIndex, setPageIndex] = useState(0)
  const sortedRuns = useMemo(
    () => [...repositoryRuns].sort(
      (left, right) => new Date(right.indexed_at) - new Date(left.indexed_at),
    ),
    [repositoryRuns],
  )
  const pageCount = Math.max(1, Math.ceil(sortedRuns.length / REPOSITORY_RUNS_PAGE_SIZE))
  const currentPage = Math.min(pageIndex, pageCount - 1)
  const visibleRuns = sortedRuns.slice(
    currentPage * REPOSITORY_RUNS_PAGE_SIZE,
    currentPage * REPOSITORY_RUNS_PAGE_SIZE + REPOSITORY_RUNS_PAGE_SIZE,
  )

  function showPreviousPage() {
    setPageIndex((current) => Math.max(0, current - 1))
  }

  function showNextPage() {
    setPageIndex((current) => Math.min(pageCount - 1, current + 1))
  }

  return (
    <section className="workspace-panel" aria-labelledby="repository-runs-title">
      <div className="workspace-header">
        <div>
          <p className="eyebrow">RAG index</p>
          <h2 id="repository-runs-title">등록된 레포지토리</h2>
        </div>
        <span>{repositoryRuns.length}개</span>
      </div>

      <div className="repository-page-toolbar">
        <button
          type="button"
          className="secondary-button compact"
          onClick={onReload}
          disabled={isLoadingRepositoryRuns}
        >
          {isLoadingRepositoryRuns ? '확인 중' : '새로고침'}
        </button>
        <div className="repository-pagination" aria-label="등록된 레포지토리 페이지 이동">
          <button type="button" onClick={showPreviousPage} disabled={currentPage === 0}>
            이전
          </button>
          <span>{currentPage + 1} / {pageCount} 페이지</span>
          <button
            type="button"
            onClick={showNextPage}
            disabled={currentPage >= pageCount - 1}
          >
            다음
          </button>
        </div>
      </div>

      {visibleRuns.length ? (
        <div className="repository-run-table">
          <div className="repository-run-header" aria-hidden="true">
            <span>레포지토리</span>
            <span>마지막 분석</span>
          </div>
          <ul className="repository-run-list repository-run-list-page">
            {visibleRuns.map((run) => (
              <li key={`${run.repository_full_name}-${run.branch || ''}`}>
                <button type="button" onClick={() => onSelectRepositoryRun(run)}>
                  <span>
                    <strong>{run.repository_full_name}</strong>
                    <small>{run.branch || '기본 브랜치'}</small>
                  </span>
                  <span className="repository-run-time">
                    <time dateTime={run.indexed_at}>{formatDateTime(run.indexed_at)}</time>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="repository-run-empty">
          아직 분석된 레포지토리가 없습니다.
        </p>
      )}
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
      <label className="repository-field-full">
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

      <div className="repository-form-actions">
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

        <button
          type="submit"
          className="primary-action repository-index-button"
          disabled={isLoading}
        >
          {isIndexing ? '분석 중' : '분석 시작'}
        </button>
      </div>

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

function formatDateTime(value) {
  if (!value) {
    return '-'
  }

  return new Intl.DateTimeFormat('ko-KR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}
