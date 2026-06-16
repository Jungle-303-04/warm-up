const BASIC_BOARD_TYPE = 1
const SCHEDULE_BOARD_TYPE = 2
const PROCEEDINGS_BOARD_TYPE = 3

// Backend: GET /board/{board_id}
// BoardDetailPage는 App.openBoardDetail()이 받은 BoardResponse DTO를 그대로 렌더링한다.
// Expected board shape:
// {
//   id: number,
//   board_type: 1 | 2 | 3,
//   title: string,
//   content: string,
//   tag?: string | null,
//   user_id: number,
//   created_at: string,
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
export function BoardDetailPage({ board, onBack }) {
  const boardTypeLabel = getBoardTypeLabel(board.board_type)

  return (
    <article className="board-detail-page" aria-labelledby="board-detail-title">
      <div className="board-detail-toolbar">
        <button type="button" className="secondary-button compact" onClick={onBack}>
          목록으로
        </button>
        <span>{boardTypeLabel}</span>
      </div>

      <header className="board-detail-header">
        <p className="eyebrow">게시글 상세</p>
        <h2 id="board-detail-title">{board.title}</h2>
        <dl className="board-detail-meta" aria-label="게시글 기본 정보">
          <div>
            <dt>게시글 ID</dt>
            <dd>{board.id}</dd>
          </div>
          <div>
            <dt>태그</dt>
            <dd>{board.tag || '-'}</dd>
          </div>
          <div>
            <dt>작성자</dt>
            <dd>{board.user_id}</dd>
          </div>
          <div>
            <dt>생성일</dt>
            <dd>{formatDateTime(board.created_at)}</dd>
          </div>
        </dl>
      </header>

      <section className="board-detail-section" aria-labelledby="board-content-title">
        <h3 id="board-content-title">본문</h3>
        <p>{board.content}</p>
      </section>

      <BoardTypeDetail board={board} />

      <section className="board-detail-section" aria-labelledby="board-relation-title">
        <h3 id="board-relation-title">관련 사용자</h3>
        <dl className="board-detail-meta">
          <div>
            <dt>담당자</dt>
            <dd>{formatIds(board.assignee_user_ids)}</dd>
          </div>
          <div>
            <dt>참여자</dt>
            <dd>{formatIds(board.participant_user_ids)}</dd>
          </div>
          <div>
            <dt>참조자</dt>
            <dd>{formatIds(board.carbon_copy_user_ids)}</dd>
          </div>
        </dl>
      </section>
    </article>
  )
}

function BoardTypeDetail({ board }) {
  if (board.board_type === SCHEDULE_BOARD_TYPE && board.schedule_board_detail) {
    return (
      <section className="board-detail-section" aria-labelledby="schedule-detail-title">
        <h3 id="schedule-detail-title">일정 정보</h3>
        <dl className="board-detail-meta">
          <div>
            <dt>시작</dt>
            <dd>{formatDateTime(board.schedule_board_detail.start_at)}</dd>
          </div>
          <div>
            <dt>종료</dt>
            <dd>{formatDateTime(board.schedule_board_detail.end_at)}</dd>
          </div>
          <div>
            <dt>중요도</dt>
            <dd>{board.schedule_board_detail.importance}</dd>
          </div>
        </dl>
        {board.schedule_board_tasks?.length ? (
          <ul className="board-task-list" aria-label="일정 작업 목록">
            {board.schedule_board_tasks.map((task) => (
              <li key={task.id}>
                <span>{task.task_name}</span>
                <strong>{getTaskStatusLabel(task.task_status)}</strong>
              </li>
            ))}
          </ul>
        ) : null}
      </section>
    )
  }

  if (board.board_type === PROCEEDINGS_BOARD_TYPE && board.proceedings_board_detail) {
    return (
      <section className="board-detail-section" aria-labelledby="proceedings-detail-title">
        <h3 id="proceedings-detail-title">회의 정보</h3>
        <dl className="board-detail-meta">
          <div>
            <dt>회의일</dt>
            <dd>{formatDateTime(board.proceedings_board_detail.meeting_date)}</dd>
          </div>
        </dl>
      </section>
    )
  }

  if (board.board_type === BASIC_BOARD_TYPE) {
    return null
  }

  return null
}

function getBoardTypeLabel(boardType) {
  if (boardType === SCHEDULE_BOARD_TYPE) {
    return '일정 게시글'
  }

  if (boardType === PROCEEDINGS_BOARD_TYPE) {
    return '회의록 게시글'
  }

  return '일반 게시글'
}

function getTaskStatusLabel(status) {
  const labels = {
    1: '대기',
    2: '진행',
    3: '완료',
    4: '보류',
  }

  return labels[status] || `상태 ${status}`
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

function formatIds(ids) {
  return ids?.length ? ids.join(', ') : '-'
}
