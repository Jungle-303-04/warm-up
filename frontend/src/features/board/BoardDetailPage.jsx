import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

import {
  BASIC_BOARD_TYPE,
  PROCEEDINGS_BOARD_TYPE,
  SCHEDULE_BOARD_TYPE,
  TASK_STATUS_OPTIONS,
  buildEmptyScheduleTask,
  buildBoardForm,
  buildUpdatePayload,
  formatDateTime,
  formatIds,
  getBoardTypeLabel,
  getTaskStatusLabel,
} from './boardForm'

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
export function BoardDetailPage({ board, isSaving, onBack, onUpdate, onDelete }) {
  const [isEditing, setIsEditing] = useState(false)
  const [form, setForm] = useState(() => buildBoardForm(board))
  const boardTypeLabel = getBoardTypeLabel(board.board_type)

  function startEditing() {
    setForm(buildBoardForm(board))
    setIsEditing(true)
  }

  function cancelEditing() {
    setForm(buildBoardForm(board))
    setIsEditing(false)
  }

  function updateField(fieldName, value) {
    setForm((current) => ({
      ...current,
      [fieldName]: value,
    }))
  }

  function addScheduleTask() {
    setForm((current) => ({
      ...current,
      scheduleTasks: [...current.scheduleTasks, buildEmptyScheduleTask()],
    }))
  }

  function updateScheduleTask(rowId, fieldName, value) {
    setForm((current) => ({
      ...current,
      scheduleTasks: current.scheduleTasks.map((task) => (
        task.rowId === rowId ? { ...task, [fieldName]: value } : task
      )),
    }))
  }

  function removeScheduleTask(rowId) {
    setForm((current) => {
      const nextTasks = current.scheduleTasks.filter((task) => task.rowId !== rowId)
      return {
        ...current,
        scheduleTasks: nextTasks.length ? nextTasks : [buildEmptyScheduleTask()],
      }
    })
  }

  async function submitUpdate(event) {
    event.preventDefault()
    const didUpdate = await onUpdate(buildUpdatePayload(board, form))
    if (didUpdate) {
      setIsEditing(false)
    }
  }

  function confirmDelete() {
    if (window.confirm('이 게시글을 삭제할까요?')) {
      onDelete()
    }
  }

  return (
    <article className="board-detail-page" aria-labelledby="board-detail-title">
      <div className="board-detail-toolbar">
        <button type="button" className="secondary-button compact" onClick={onBack}>
          목록으로
        </button>
        <div className="board-detail-actions" aria-label="게시글 작업">
          <span>{boardTypeLabel}</span>
          {!isEditing ? (
            <button
              type="button"
              className="secondary-button compact"
              onClick={startEditing}
            >
              수정
            </button>
          ) : null}
          <button
            type="button"
            className="danger-button compact"
            onClick={confirmDelete}
            disabled={isSaving}
          >
            삭제
          </button>
        </div>
      </div>

      {isEditing ? (
        <BoardEditForm
          board={board}
          form={form}
          isSaving={isSaving}
          onChange={updateField}
          onAddScheduleTask={addScheduleTask}
          onUpdateScheduleTask={updateScheduleTask}
          onRemoveScheduleTask={removeScheduleTask}
          onCancel={cancelEditing}
          onSubmit={submitUpdate}
        />
      ) : (
        <BoardReadView board={board} />
      )}
    </article>
  )
}

function BoardReadView({ board }) {
  return (
    <>
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
        <div className="markdown-viewer">
          <ReactMarkdown>{board.content}</ReactMarkdown>
        </div>
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
    </>
  )
}

function BoardEditForm({
  board,
  form,
  isSaving,
  onChange,
  onAddScheduleTask,
  onUpdateScheduleTask,
  onRemoveScheduleTask,
  onCancel,
  onSubmit,
}) {
  return (
    <form className="board-edit-form" onSubmit={onSubmit}>
      <header className="board-detail-header">
        <p className="eyebrow">게시글 수정</p>
        <label className="board-field">
          <span>제목</span>
          <input
            type="text"
            value={form.title}
            onChange={(event) => onChange('title', event.target.value)}
            required
          />
        </label>
        <label className="board-field">
          <span>태그</span>
          <input
            type="text"
            value={form.tag}
            onChange={(event) => onChange('tag', event.target.value)}
            placeholder="태그 없음"
          />
        </label>
      </header>

      <section className="board-detail-section">
        <label className="board-field">
          <span>본문</span>
          <textarea
            value={form.content}
            onChange={(event) => onChange('content', event.target.value)}
            required
            rows={6}
          />
        </label>
      </section>

      <BoardTypeEditFields
        board={board}
        form={form}
        onChange={onChange}
        onAddScheduleTask={onAddScheduleTask}
        onUpdateScheduleTask={onUpdateScheduleTask}
        onRemoveScheduleTask={onRemoveScheduleTask}
      />

      <section className="board-detail-section">
        <h3>관련 사용자</h3>
        <div className="board-field-grid">
          <label className="board-field">
            <span>담당자 ID</span>
            <input
              type="text"
              value={form.assigneeUserIds}
              onChange={(event) => onChange('assigneeUserIds', event.target.value)}
              placeholder="1, 2"
            />
          </label>
          <label className="board-field">
            <span>참여자 ID</span>
            <input
              type="text"
              value={form.participantUserIds}
              onChange={(event) => onChange('participantUserIds', event.target.value)}
              placeholder="1, 2"
            />
          </label>
          <label className="board-field">
            <span>참조자 ID</span>
            <input
              type="text"
              value={form.carbonCopyUserIds}
              onChange={(event) => onChange('carbonCopyUserIds', event.target.value)}
              placeholder="1, 2"
            />
          </label>
        </div>
      </section>

      <div className="board-form-actions">
        <button
          type="button"
          className="secondary-button compact"
          onClick={onCancel}
          disabled={isSaving}
        >
          취소
        </button>
        <button type="submit" className="primary-action board-save-button" disabled={isSaving}>
          {isSaving ? '저장 중' : '저장'}
        </button>
      </div>
    </form>
  )
}

function BoardTypeEditFields({
  board,
  form,
  onChange,
  onAddScheduleTask,
  onUpdateScheduleTask,
  onRemoveScheduleTask,
}) {
  if (board.board_type === SCHEDULE_BOARD_TYPE) {
    return (
      <section className="board-detail-section">
        <h3>일정 정보</h3>
        <div className="board-field-grid">
          <label className="board-field">
            <span>시작</span>
            <input
              type="datetime-local"
              value={form.scheduleStartAt}
              onChange={(event) => onChange('scheduleStartAt', event.target.value)}
              required
            />
          </label>
          <label className="board-field">
            <span>종료</span>
            <input
              type="datetime-local"
              value={form.scheduleEndAt}
              onChange={(event) => onChange('scheduleEndAt', event.target.value)}
              required
            />
          </label>
          <label className="board-field">
            <span>중요도</span>
            <input
              type="number"
              min="1"
              max="10"
              value={form.importance}
              onChange={(event) => onChange('importance', event.target.value)}
              required
            />
          </label>
        </div>
        <ScheduleTaskRows
          tasks={form.scheduleTasks}
          onAdd={onAddScheduleTask}
          onUpdate={onUpdateScheduleTask}
          onRemove={onRemoveScheduleTask}
        />
      </section>
    )
  }

  if (board.board_type === PROCEEDINGS_BOARD_TYPE) {
    return (
      <section className="board-detail-section">
        <h3>회의 정보</h3>
        <label className="board-field">
          <span>회의일</span>
          <input
            type="datetime-local"
            value={form.meetingDate}
            onChange={(event) => onChange('meetingDate', event.target.value)}
            required
          />
        </label>
      </section>
    )
  }

  return null
}

function ScheduleTaskRows({ tasks, onAdd, onUpdate, onRemove }) {
  return (
    <section className="schedule-task-editor" aria-labelledby="schedule-task-edit-title">
      <div className="schedule-task-editor-header">
        <h4 id="schedule-task-edit-title">작업 목록</h4>
        <button type="button" className="secondary-button compact" onClick={onAdd}>
          작업 추가
        </button>
      </div>

      <div className="schedule-task-rows">
        {tasks.map((task, index) => (
          <div className="schedule-task-row" key={task.rowId}>
            <label className="board-field">
              <span>{index + 1}번째 작업</span>
              <input
                type="text"
                value={task.taskName}
                onChange={(event) => onUpdate(task.rowId, 'taskName', event.target.value)}
                placeholder="작업명을 입력하세요"
              />
            </label>
            <label className="board-field">
              <span>상태</span>
              <select
                value={task.taskStatus}
                onChange={(event) => onUpdate(task.rowId, 'taskStatus', event.target.value)}
              >
                {TASK_STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="danger-button compact"
              onClick={() => onRemove(task.rowId)}
              aria-label={`${index + 1}번째 작업 삭제`}
            >
              삭제
            </button>
          </div>
        ))}
      </div>
    </section>
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
