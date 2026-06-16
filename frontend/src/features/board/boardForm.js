export const BASIC_BOARD_TYPE = 1
export const SCHEDULE_BOARD_TYPE = 2
export const PROCEEDINGS_BOARD_TYPE = 3
export const TASK_STATUS_OPTIONS = [
  { value: '1', label: '대기' },
  { value: '2', label: '진행' },
  { value: '3', label: '완료' },
  { value: '4', label: '보류' },
]

export function buildBoardForm(board) {
  return {
    title: board.title || '',
    content: board.content || '',
    tag: board.tag || '',
    assigneeUserIds: formatIdsForInput(board.assignee_user_ids),
    participantUserIds: formatIdsForInput(board.participant_user_ids),
    carbonCopyUserIds: formatIdsForInput(board.carbon_copy_user_ids),
    scheduleStartAt: toDateTimeInputValue(board.schedule_board_detail?.start_at),
    scheduleEndAt: toDateTimeInputValue(board.schedule_board_detail?.end_at),
    importance: String(board.schedule_board_detail?.importance || 5),
    scheduleTasks: formatTasksForInput(board.schedule_board_tasks),
    meetingDate: toDateTimeInputValue(board.proceedings_board_detail?.meeting_date),
  }
}

export function buildCreateForm(initialStartDate = null) {
  const start = initialStartDate ? new Date(initialStartDate) : new Date()
  if (initialStartDate) {
    start.setHours(9, 0, 0, 0)
  } else {
    start.setMinutes(0, 0, 0)
  }
  const end = new Date(start)
  end.setHours(start.getHours() + 1)

  return {
    boardType: String(SCHEDULE_BOARD_TYPE),
    title: '',
    content: '',
    tag: '',
    assigneeUserIds: '',
    participantUserIds: '',
    carbonCopyUserIds: '',
    scheduleStartAt: toDateTimeInputValue(start.toISOString()),
    scheduleEndAt: toDateTimeInputValue(end.toISOString()),
    importance: '5',
    scheduleTasks: [buildEmptyScheduleTask()],
    meetingDate: toDateTimeInputValue(start.toISOString()),
  }
}

export function buildCreatePayload(form) {
  return buildBoardPayload(Number(form.boardType), form)
}

export function buildUpdatePayload(board, form) {
  return buildBoardPayload(board.board_type, form)
}

export function getBoardTypeLabel(boardType) {
  if (boardType === SCHEDULE_BOARD_TYPE) {
    return '일정 게시글'
  }

  if (boardType === PROCEEDINGS_BOARD_TYPE) {
    return '회의록 게시글'
  }

  return '일반 게시글'
}

export function getTaskStatusLabel(status) {
  const labels = {
    1: '대기',
    2: '진행',
    3: '완료',
    4: '보류',
  }

  return labels[status] || `상태 ${status}`
}

export function formatDateTime(value) {
  if (!value) {
    return '-'
  }

  return new Intl.DateTimeFormat('ko-KR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export function formatIds(ids) {
  return ids?.length ? ids.join(', ') : '-'
}

function buildBoardPayload(boardType, form) {
  const payload = {
    board_type: boardType,
    title: form.title.trim(),
    content: form.content.trim(),
    tag: form.tag.trim() || null,
    assignee_user_ids: parseIdList(form.assigneeUserIds),
    participant_user_ids: parseIdList(form.participantUserIds),
    carbon_copy_user_ids: parseIdList(form.carbonCopyUserIds),
    schedule_board_detail: null,
    schedule_board_tasks: [],
    proceedings_board_detail: null,
  }

  if (boardType === SCHEDULE_BOARD_TYPE) {
    payload.schedule_board_detail = {
      start_at: toApiDateTime(form.scheduleStartAt),
      end_at: toApiDateTime(form.scheduleEndAt),
      importance: Number(form.importance),
    }
    payload.schedule_board_tasks = parseTaskRows(form.scheduleTasks)
  }

  if (boardType === PROCEEDINGS_BOARD_TYPE) {
    payload.proceedings_board_detail = {
      meeting_date: toApiDateTime(form.meetingDate),
    }
  }

  return payload
}

function formatIdsForInput(ids) {
  return ids?.length ? ids.join(', ') : ''
}

function parseIdList(value) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
    .map(Number)
    .filter((item) => Number.isInteger(item) && item > 0)
}

function formatTasksForInput(tasks) {
  return tasks?.length
    ? tasks.map((task) => ({
      rowId: buildScheduleTaskRowId(),
      taskName: task.task_name || '',
      taskStatus: String(task.task_status || 1),
    }))
    : [buildEmptyScheduleTask()]
}

function parseTaskRows(tasks) {
  return tasks
    .map((task) => ({
      task_name: task.taskName.trim(),
      task_status: clampTaskStatus(Number(task.taskStatus)),
    }))
    .filter((task) => task.task_name)
}

export function buildEmptyScheduleTask() {
  return {
    rowId: buildScheduleTaskRowId(),
    taskName: '',
    taskStatus: '1',
  }
}

function buildScheduleTaskRowId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

function clampTaskStatus(value) {
  if (!Number.isInteger(value)) {
    return 1
  }

  return Math.min(Math.max(value, 1), 4)
}

function toDateTimeInputValue(value) {
  if (!value) {
    return ''
  }

  const date = new Date(value)
  const offsetDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
  return offsetDate.toISOString().slice(0, 16)
}

function toApiDateTime(value) {
  return new Date(value).toISOString()
}
