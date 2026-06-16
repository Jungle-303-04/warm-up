import { useMemo, useState } from 'react'

import { BOARD_TYPE_FILTERS, filterBoards } from '../board/boardFilters'
import {
  BASIC_BOARD_TYPE,
  PROCEEDINGS_BOARD_TYPE,
  SCHEDULE_BOARD_TYPE,
  calculateScheduleTaskProgress,
} from '../board/boardForm'

const WEEKDAY_LABELS = ['일', '월', '화', '수', '목', '금', '토']
const CALENDAR_WEEK_BASE_HEIGHT = 116
const CALENDAR_WEEK_HEADER_SPACE = 44
const CALENDAR_WEEK_BLOCK_SPACE = 16
const CALENDAR_EVENT_ROW_HEIGHT = 22
const CALENDAR_EVENT_ROW_GAP = 4

export function CalendarWorkspace({
  boards,
  visibleMonth,
  isLoadingBoards,
  onPreviousMonth,
  onNextMonth,
  onCurrentMonth,
  onReloadBoards,
  onStartCreateBoard,
  onOpenBoard,
}) {
  const [boardTypeFilter, setBoardTypeFilter] = useState('all')
  const [searchKeyword, setSearchKeyword] = useState('')
  const filteredBoards = useMemo(
    () => filterBoards(boards, boardTypeFilter, searchKeyword),
    [boards, boardTypeFilter, searchKeyword],
  )
  const calendarEvents = filteredBoards.flatMap(mapBoardToCalendarEvents)
  const monthLabel = formatMonthLabel(visibleMonth)
  const weeks = buildCalendarWeeks(visibleMonth)
  const weekSegments = weeks.map((week) =>
    buildWeekSegments(week, calendarEvents),
  )
  const monthEvents = calendarEvents.filter((event) =>
    isEventVisibleInMonth(event, visibleMonth),
  )
  const scheduleCount = monthEvents.filter((event) => event.type === 'schedule').length
  const meetingCount = monthEvents.filter((event) => event.type === 'meeting').length

  return (
    <section className="calendar-panel" aria-labelledby="calendar-title">
      <div className="calendar-toolbar">
        <div>
          <p className="eyebrow">게시글 일정</p>
          <h2 id="calendar-title">캘린더</h2>
        </div>
        <div className="calendar-actions" aria-label="달력 이동">
          <button type="button" onClick={onPreviousMonth}>
            이전
          </button>
          <strong>{monthLabel}</strong>
          <button type="button" onClick={onNextMonth}>
            다음
          </button>
          <button type="button" onClick={onCurrentMonth}>
            오늘
          </button>
          <button type="button" onClick={onReloadBoards} disabled={isLoadingBoards}>
            {isLoadingBoards ? '불러오는 중' : '새로고침'}
          </button>
          <button type="button" className="primary-calendar-action" onClick={onStartCreateBoard}>
            게시글 추가
          </button>
        </div>
      </div>

      <dl className="calendar-summary" aria-label="이번 달 게시글 일정 요약">
        <div>
          <dt>이번 달 일정</dt>
          <dd>{scheduleCount}</dd>
        </div>
        <div>
          <dt>회의록</dt>
          <dd>{meetingCount}</dd>
        </div>
        <div>
          <dt>전체 게시글</dt>
          <dd>{boards.length}</dd>
        </div>
      </dl>

      <div className="calendar-filter-row">
        <div className="calendar-legend" aria-label="캘린더 표시 구분">
          <span>
            <i className="legend-schedule" />
            일정
          </span>
          <span>
            <i className="legend-meeting" />
            회의록
          </span>
          <span>
            <i className="legend-basic" />
            일반
          </span>
        </div>

        <fieldset className="calendar-type-filter" aria-label="게시글 유형 필터">
          {BOARD_TYPE_FILTERS.map((filter) => (
            <label key={filter.value}>
              <input
                type="radio"
                name="calendar-board-type"
                value={filter.value}
                checked={boardTypeFilter === filter.value}
                onChange={(event) => setBoardTypeFilter(event.target.value)}
              />
              <span>{filter.label}</span>
            </label>
          ))}
        </fieldset>

        <label className="board-search-box calendar-search-box">
          <span className="visually-hidden">게시글 검색</span>
          <IconSearch />
          <input
            type="search"
            value={searchKeyword}
            onChange={(event) => setSearchKeyword(event.target.value)}
            placeholder="제목, 내용, 태그, 작성자"
          />
        </label>
      </div>

      <div className="calendar-grid" role="grid" aria-label={`${monthLabel} 달력`}>
        {WEEKDAY_LABELS.map((label) => (
          <div className="calendar-weekday" key={label} role="columnheader">
            {label}
          </div>
        ))}

        {weeks.map((week, weekIndex) => (
          <CalendarWeek
            key={week[0].dateKey}
            week={week}
            segments={weekSegments[weekIndex]}
            visibleMonth={visibleMonth}
            onStartCreateBoard={onStartCreateBoard}
            onOpenBoard={onOpenBoard}
          />
        ))}
      </div>

      {monthEvents.length === 0 ? (
        <p className="calendar-empty">
          이번 달 달력에 표시할 일정이나 회의록이 없습니다.
        </p>
      ) : null}
    </section>
  )
}

function CalendarWeek({ week, segments, visibleMonth, onStartCreateBoard, onOpenBoard }) {
  const eventRowCount = Math.max(1, ...segments.map((segment) => segment.row))
  const weekMinHeight = Math.max(
    CALENDAR_WEEK_BASE_HEIGHT,
    CALENDAR_WEEK_HEADER_SPACE
      + CALENDAR_WEEK_BLOCK_SPACE
      + (eventRowCount * CALENDAR_EVENT_ROW_HEIGHT)
      + ((eventRowCount - 1) * CALENDAR_EVENT_ROW_GAP),
  )

  return (
    <div
      className="calendar-week"
      role="row"
      style={{
        '--calendar-week-min-height': `${weekMinHeight}px`,
        '--calendar-event-row-count': eventRowCount,
      }}
    >
      {week.map((day) => (
        <div
          className={`calendar-day ${
            day.month === visibleMonth.getMonth() ? '' : 'outside-month'
          }`}
          key={day.dateKey}
          role="gridcell"
        >
          <button
            type="button"
            className="calendar-day-button"
            onClick={() => onStartCreateBoard(day.date)}
            aria-label={`${formatDateLabel(day.date)} 게시글 작성`}
          >
            <span>{day.date.getDate()}</span>
          </button>
        </div>
      ))}

      <div className="calendar-event-layer" aria-label="게시글 일정 목록">
        {segments.map((segment) => (
          <button
            type="button"
            className={`calendar-event calendar-event-${segment.event.type}`}
            key={`${segment.event.id}-${segment.weekStartKey}`}
            style={{
              gridColumn: `${segment.startColumn} / span ${segment.span}`,
              gridRow: segment.row,
              '--calendar-event-bg': segment.event.color.background,
              '--calendar-event-border': segment.event.color.border,
            }}
            onClick={() => onOpenBoard(segment.event.boardId)}
          >
            <span>{segment.label}</span>
            {Number.isInteger(segment.event.progressPercent) ? (
              <strong>{segment.event.progressPercent}%</strong>
            ) : null}
          </button>
        ))}
      </div>
    </div>
  )
}

function mapBoardToCalendarEvents(board) {
  if (board.board_type === BASIC_BOARD_TYPE) {
    return [mapBasicBoardToCalendarEvent(board)]
  }

  if (board.board_type === SCHEDULE_BOARD_TYPE && board.schedule_board_detail) {
    return [mapScheduleBoardToCalendarEvent(board)]
  }

  if (board.board_type === PROCEEDINGS_BOARD_TYPE && board.proceedings_board_detail) {
    return [mapProceedingsBoardToCalendarEvent(board)]
  }

  return []
}

// Backend: GET /board/
// Response item 중 일반 게시글은 별도 일정 날짜가 없으므로 created_at 하루에 표시한다.
// 캘린더의 "일반" 필터와 범례가 실제 화면 결과와 어긋나지 않게 하기 위한 매핑이다.
function mapBasicBoardToCalendarEvent(board) {
  return {
    id: `basic-${board.id}`,
    boardId: board.id,
    type: 'basic',
    color: getBoardEventColor('basic', board),
    title: board.title,
    content: board.content,
    tag: board.tag,
    startAt: board.created_at,
    endAt: board.created_at,
  }
}

// Backend: GET /board/
// Response item 중 일정 게시글은 아래 값을 가진다.
// {
//   id: number,
//   board_type: 2,
//   title: string,
//   content: string,
//   tag?: string | null, // "#기획 #회의"처럼 #으로 구분된 복수 태그 문자열
//   user_id: number,
//   author_display_name?: string | null,
//   author_login?: string | null,
//   author_name?: string | null,
//   schedule_board_detail: {
//     start_at: string,
//     end_at: string,
//     importance: number
//   },
//   schedule_board_tasks?: Array<{
//     task_name: string,
//     task_status: 1 | 2 | 3 | 4
//   }>
// }
// 화면에서는 start_at부터 end_at까지 이어지는 일정 막대로 표시한다.
// schedule_board_tasks가 있으면 완료=100%, 진행=50%, 대기/보류=0% 기준으로 진행률을 함께 표시한다.
// 사용자가 막대를 클릭하면 board.id를 GET /board/{board_id} 상세 조회에 넘긴다.
function mapScheduleBoardToCalendarEvent(board) {
  const progressPercent = calculateScheduleTaskProgress(board.schedule_board_tasks)

  return {
    id: `schedule-${board.id}`,
    boardId: board.id,
    type: 'schedule',
    color: getBoardEventColor('schedule', board),
    title: board.title,
    content: board.content,
    tag: board.tag,
    startAt: board.schedule_board_detail.start_at,
    endAt: board.schedule_board_detail.end_at,
    importance: board.schedule_board_detail.importance,
    progressPercent,
  }
}

// Backend: GET /board/
// Response item 중 회의록 게시글은 아래 값을 가진다.
// {
//   id: number,
//   board_type: 3,
//   title: string,
//   content: string,
//   tag?: string | null, // "#기획 #회의"처럼 #으로 구분된 복수 태그 문자열
//   user_id: number,
//   proceedings_board_detail: {
//     meeting_date: string
//   }
// }
// 화면에서는 meeting_date 하루에 회의록 이벤트로 표시한다.
// 사용자가 이벤트를 클릭하면 board.id를 GET /board/{board_id} 상세 조회에 넘긴다.
function mapProceedingsBoardToCalendarEvent(board) {
  return {
    id: `meeting-${board.id}`,
    boardId: board.id,
    type: 'meeting',
    color: getBoardEventColor('meeting', board),
    title: board.title,
    content: board.content,
    tag: board.tag,
    startAt: board.proceedings_board_detail.meeting_date,
    endAt: board.proceedings_board_detail.meeting_date,
  }
}

function buildCalendarWeeks(monthDate) {
  const firstDay = new Date(monthDate.getFullYear(), monthDate.getMonth(), 1)
  const firstCalendarDay = new Date(firstDay)
  firstCalendarDay.setDate(firstDay.getDate() - firstDay.getDay())

  return Array.from({ length: 6 }, (_, weekIndex) =>
    Array.from({ length: 7 }, (_, dayIndex) => {
      const date = new Date(firstCalendarDay)
      date.setDate(firstCalendarDay.getDate() + weekIndex * 7 + dayIndex)
      return {
        date,
        dateKey: toDateKey(date),
        month: date.getMonth(),
      }
    }),
  )
}

function buildWeekSegments(week, events) {
  const weekStart = startOfDay(week[0].date)
  const weekEnd = startOfDay(week[6].date)
  const usedRows = []

  return events
    .map((event) => buildWeekSegment(weekStart, weekEnd, event))
    .filter(Boolean)
    .sort((a, b) => a.startColumn - b.startColumn || b.span - a.span)
    .map((segment) => {
      const row = findAvailableRow(usedRows, segment)
      usedRows[row] = usedRows[row] || []
      usedRows[row].push(segment)
      return { ...segment, row: row + 1 }
    })
}

function buildWeekSegment(weekStart, weekEnd, event) {
  const eventStart = startOfDay(new Date(event.startAt))
  const eventEnd = startOfDay(new Date(event.endAt))

  if (eventEnd < weekStart || eventStart > weekEnd) {
    return null
  }

  const segmentStart = eventStart < weekStart ? weekStart : eventStart
  const segmentEnd = eventEnd > weekEnd ? weekEnd : eventEnd
  const startColumn = daysBetween(weekStart, segmentStart) + 1
  const span = daysBetween(segmentStart, segmentEnd) + 1

  return {
    event,
    weekStartKey: toDateKey(weekStart),
    startColumn,
    span,
    label: formatEventLabel(event),
  }
}

function formatEventLabel(event) {
  if (event.type === 'meeting') {
    return `회의 ${event.title}`
  }

  if (event.type === 'basic') {
    return `일반 ${event.title}`
  }

  return event.title
}

const EVENT_COLOR_PALETTES = {
  schedule: [
    { background: '#2FBF71', border: '#1F8F55' },
    { background: '#249E63', border: '#19794B' },
    { background: '#58C98C', border: '#2B9A62' },
    { background: '#1F7F5C', border: '#176246' },
    { background: '#39AC6E', border: '#247C50' },
  ],
  meeting: [
    { background: '#315F9C', border: '#214878' },
    { background: '#3E78B2', border: '#285C8C' },
    { background: '#254F85', border: '#1B3B66' },
    { background: '#4D8AC7', border: '#32699D' },
    { background: '#2D6F91', border: '#20536E' },
  ],
  basic: [
    { background: '#747D88', border: '#59636F' },
    { background: '#5F6B78', border: '#48525E' },
    { background: '#8A7E70', border: '#6D6256' },
    { background: '#66727C', border: '#4D5964' },
    { background: '#7C7485', border: '#615A6A' },
  ],
}

function getEventColor(type, boardId) {
  const palette = EVENT_COLOR_PALETTES[type] || EVENT_COLOR_PALETTES.basic
  const colorIndex = Math.abs(Number(boardId) || 0) % palette.length
  return palette[colorIndex]
}

function getBoardEventColor(type, board) {
  if (board.ui_event_color) {
    return {
      background: board.ui_event_color,
      border: darkenHexColor(board.ui_event_color),
    }
  }

  return getEventColor(type, board.id)
}

function darkenHexColor(hexColor) {
  const color = hexColor.replace('#', '')
  const red = Math.max(0, Math.round(parseInt(color.slice(0, 2), 16) * 0.72))
  const green = Math.max(0, Math.round(parseInt(color.slice(2, 4), 16) * 0.72))
  const blue = Math.max(0, Math.round(parseInt(color.slice(4, 6), 16) * 0.72))

  return `#${toHexPair(red)}${toHexPair(green)}${toHexPair(blue)}`
}

function toHexPair(value) {
  return value.toString(16).padStart(2, '0')
}

function isEventVisibleInMonth(event, visibleMonth) {
  const monthStart = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth(), 1)
  const monthEnd = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 0)
  const eventStart = startOfDay(new Date(event.startAt))
  const eventEnd = startOfDay(new Date(event.endAt))

  return eventStart <= monthEnd && eventEnd >= monthStart
}

function findAvailableRow(usedRows, segment) {
  const start = segment.startColumn
  const end = segment.startColumn + segment.span - 1
  const rowIndex = usedRows.findIndex((row) =>
    row.every((item) => item.startColumn + item.span - 1 < start || item.startColumn > end),
  )

  return rowIndex === -1 ? usedRows.length : rowIndex
}

function formatMonthLabel(date) {
  return `${date.getFullYear()}년 ${date.getMonth() + 1}월`
}

function formatDateLabel(date) {
  return `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일`
}

function startOfDay(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}

function daysBetween(start, end) {
  return Math.round((startOfDay(end) - startOfDay(start)) / 86400000)
}

function toDateKey(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function IconSearch() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="11" cy="11" r="6" />
      <path d="m16 16 4 4" />
    </svg>
  )
}
