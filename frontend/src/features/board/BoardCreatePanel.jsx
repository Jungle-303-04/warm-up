import { useState } from 'react'

import {
  BASIC_BOARD_TYPE,
  PROCEEDINGS_BOARD_TYPE,
  SCHEDULE_BOARD_TYPE,
  buildCreateForm,
  buildCreatePayload,
} from './boardForm'

export function BoardCreatePanel({ initialStartDate, isSaving, onCancel, onCreate }) {
  const [form, setForm] = useState(() => buildCreateForm(initialStartDate))
  const boardType = Number(form.boardType)

  function updateField(fieldName, value) {
    setForm((current) => ({
      ...current,
      [fieldName]: value,
    }))
  }

  async function submitCreate(event) {
    event.preventDefault()
    // Backend: POST /board/
    // buildCreatePayload(form)은 CreateBoard DTO 모양으로 값을 변환한다.
    // {
    //   board_type: 1 | 2 | 3,
    //   title: string,
    //   content: string,
    //   tag?: string | null,
    //   assignee_user_ids: number[],
    //   participant_user_ids: number[],
    //   carbon_copy_user_ids: number[],
    //   schedule_board_detail?: {
    //     start_at: string,
    //     end_at: string,
    //     importance: number
    //   } | null,
    //   schedule_board_tasks: Array<{
    //     task_name: string,
    //     task_status: 1 | 2 | 3 | 4
    //   }>,
    //   proceedings_board_detail?: {
    //     meeting_date: string
    //   } | null
    // }
    // 로그인 사용자는 user_id를 직접 보내지 않고, 백엔드가 auth cookie로 해석한다.
    const didCreate = await onCreate(buildCreatePayload(form))
    if (didCreate) {
      setForm(buildCreateForm())
    }
  }

  return (
    <article className="board-detail-page" aria-labelledby="board-create-title">
      <form className="board-edit-form" onSubmit={submitCreate}>
        <header className="board-create-header">
          <div>
            <p className="eyebrow">새 게시글</p>
            <h2 id="board-create-title">캘린더에 등록할 게시글 추가</h2>
          </div>
          <button
            type="button"
            className="secondary-button compact"
            onClick={onCancel}
            disabled={isSaving}
          >
            목록으로
          </button>
        </header>

        <div className="board-field-grid">
          <label className="board-field">
            <span>게시글 종류</span>
            <select
              value={form.boardType}
              onChange={(event) => updateField('boardType', event.target.value)}
            >
              <option value={SCHEDULE_BOARD_TYPE}>일정 게시글</option>
              <option value={PROCEEDINGS_BOARD_TYPE}>회의록 게시글</option>
              <option value={BASIC_BOARD_TYPE}>일반 게시글</option>
            </select>
          </label>
          <label className="board-field">
            <span>태그</span>
            <input
              type="text"
              value={form.tag}
              onChange={(event) => updateField('tag', event.target.value)}
              placeholder="calendar"
            />
          </label>
        </div>

        <label className="board-field">
          <span>제목</span>
          <input
            type="text"
            value={form.title}
            onChange={(event) => updateField('title', event.target.value)}
            required
          />
        </label>

        <label className="board-field">
          <span>본문</span>
          <textarea
            value={form.content}
            onChange={(event) => updateField('content', event.target.value)}
            required
            rows={5}
          />
        </label>

        <BoardCreateTypeFields
          boardType={boardType}
          form={form}
          onChange={updateField}
        />

        <section className="board-detail-section">
          <h3>관련 사용자</h3>
          <div className="board-field-grid">
            <label className="board-field">
              <span>담당자 ID</span>
              <input
                type="text"
                value={form.assigneeUserIds}
                onChange={(event) => updateField('assigneeUserIds', event.target.value)}
                placeholder="1, 2"
              />
            </label>
            <label className="board-field">
              <span>참여자 ID</span>
              <input
                type="text"
                value={form.participantUserIds}
                onChange={(event) => updateField('participantUserIds', event.target.value)}
                placeholder="1, 2"
              />
            </label>
            <label className="board-field">
              <span>참조자 ID</span>
              <input
                type="text"
                value={form.carbonCopyUserIds}
                onChange={(event) => updateField('carbonCopyUserIds', event.target.value)}
                placeholder="1, 2"
              />
            </label>
          </div>
        </section>

        <button type="submit" className="primary-action board-save-button" disabled={isSaving}>
          {isSaving ? '등록 중' : '게시글 등록'}
        </button>
      </form>
    </article>
  )
}

function BoardCreateTypeFields({ boardType, form, onChange }) {
  if (boardType === SCHEDULE_BOARD_TYPE) {
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
        <label className="board-field">
          <span>작업 목록</span>
          <textarea
            value={form.scheduleTasks}
            onChange={(event) => onChange('scheduleTasks', event.target.value)}
            placeholder={'작업명|상태번호\n캘린더 이벤트 매핑|2'}
            rows={4}
          />
        </label>
      </section>
    )
  }

  if (boardType === PROCEEDINGS_BOARD_TYPE) {
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
