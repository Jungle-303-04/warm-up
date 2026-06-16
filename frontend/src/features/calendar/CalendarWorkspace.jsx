import { useMemo, useState } from 'react'

const BASIC_BOARD_TYPE = 1
const SCHEDULE_BOARD_TYPE = 2
const PROCEEDINGS_BOARD_TYPE = 3
const WEEKDAY_LABELS = ['일', '월', '화', '수', '목', '금', '토']
const BOARD_TYPE_FILTERS = [
  { value: 'all', label: '전체' },
  { value: 'meeting', label: '회의록' },
  { value: 'schedule', label: '일정' },
  { value: 'basic', label: '일반' },
]

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
  const [tagKeyword, setTagKeyword] = useState('')
  const filteredBoards = useMemo(
    () => filterBoards(boards, boardTypeFilter, searchKeyword, tagKeyword),
    [boards, boardTypeFilter, searchKeyword, tagKeyword],
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
  const basicCount = filteredBoards.filter((board) => board.board_type === BASIC_BOARD_TYPE).length

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
      </div>

      <div className="calendar-search-panel" aria-label="게시글 검색">
        <label>
          <span>검색</span>
          <input
            type="search"
            value={searchKeyword}
            onChange={(event) => setSearchKeyword(event.target.value)}
            placeholder="제목 또는 내용 입력"
          />
        </label>
        <label>
          <span>태그</span>
          <input
            type="search"
            value={tagKeyword}
            onChange={(event) => setTagKeyword(event.target.value)}
            placeholder="태그"
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
            onOpenBoard={onOpenBoard}
          />
        ))}
      </div>

      {monthEvents.length === 0 ? (
        <p className="calendar-empty">
          이번 달 달력에 표시할 일정이나 회의록이 없습니다.
        </p>
      ) : null}

      <CalendarBoardResults
        boards={filteredBoards}
        basicCount={basicCount}
        onOpenBoard={onOpenBoard}
      />
    </section>
  )
}

function CalendarBoardResults({ boards, basicCount, onOpenBoard }) {
  if (!boards.length) {
    return (
      <p className="calendar-empty">
        조건에 맞는 게시글이 없습니다.
      </p>
    )
  }

  return (
    <section className="calendar-result-panel" aria-labelledby="calendar-result-title">
      <div className="calendar-result-header">
        <h3 id="calendar-result-title">필터 결과</h3>
        <span>전체 {boards.length}개 · 일반 {basicCount}개</span>
      </div>
      <ul className="calendar-result-list">
        {boards.slice(0, 8).map((board) => (
          <li key={board.id}>
            <button type="button" onClick={() => onOpenBoard(board.id)}>
              <strong>{board.title}</strong>
              <span>
                {getBoardTypeLabel(board.board_type)}
                {board.tag ? ` · #${board.tag}` : ''}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}

function CalendarWeek({ week, segments, visibleMonth, onOpenBoard }) {
  return (
    <div className="calendar-week" role="row">
      {week.map((day) => (
        <div
          className={`calendar-day ${
            day.month === visibleMonth.getMonth() ? '' : 'outside-month'
          }`}
          key={day.dateKey}
          role="gridcell"
        >
          <span>{day.date.getDate()}</span>
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
            }}
            onClick={() => onOpenBoard(segment.event.boardId)}
          >
            {segment.label}
          </button>
        ))}
      </div>
    </div>
  )
}

function mapBoardToCalendarEvents(board) {
  if (board.board_type === SCHEDULE_BOARD_TYPE && board.schedule_board_detail) {
    return [mapScheduleBoardToCalendarEvent(board)]
  }

  if (board.board_type === PROCEEDINGS_BOARD_TYPE && board.proceedings_board_detail) {
    return [mapProceedingsBoardToCalendarEvent(board)]
  }

  return []
}

function filterBoards(boards, boardTypeFilter, searchKeyword, tagKeyword) {
  // Backend: GET /board/
  // Response items already include title, content, tag, board_type, and detail DTOs.
  // These controls filter the loaded board DTOs on the frontend only.
  const normalizedSearchKeyword = normalizeSearchValue(searchKeyword)
  const normalizedTagKeyword = normalizeSearchValue(tagKeyword)

  return boards.filter((board) => {
    if (!matchesBoardType(board, boardTypeFilter)) {
      return false
    }

    if (normalizedSearchKeyword) {
      const haystack = normalizeSearchValue(`${board.title} ${board.content}`)
      if (!haystack.includes(normalizedSearchKeyword)) {
        return false
      }
    }

    if (normalizedTagKeyword) {
      const tag = normalizeSearchValue(board.tag || '')
      if (!tag.includes(normalizedTagKeyword)) {
        return false
      }
    }

    return true
  })
}

function matchesBoardType(board, boardTypeFilter) {
  if (boardTypeFilter === 'all') {
    return true
  }

  if (boardTypeFilter === 'basic') {
    return board.board_type === BASIC_BOARD_TYPE
  }

  if (boardTypeFilter === 'schedule') {
    return board.board_type === SCHEDULE_BOARD_TYPE
  }

  return board.board_type === PROCEEDINGS_BOARD_TYPE
}

function normalizeSearchValue(value) {
  return value.trim().toLowerCase()
}

function getBoardTypeLabel(boardType) {
  if (boardType === SCHEDULE_BOARD_TYPE) {
    return '일정'
  }

  if (boardType === PROCEEDINGS_BOARD_TYPE) {
    return '회의록'
  }

  return '일반'
}

// Backend: GET /board/
// Response item 중 일정 게시글은 아래 값을 가진다.
// {
//   id: number,
//   board_type: 2,
//   title: string,
//   content: string,
//   tag?: string | null,
//   user_id: number,
//   schedule_board_detail: {
//     start_at: string,
//     end_at: string,
//     importance: number
//   }
// }
// 화면에서는 start_at부터 end_at까지 이어지는 일정 막대로 표시한다.
// 사용자가 막대를 클릭하면 board.id를 GET /board/{board_id} 상세 조회에 넘긴다.
function mapScheduleBoardToCalendarEvent(board) {
  return {
    id: `schedule-${board.id}`,
    boardId: board.id,
    type: 'schedule',
    title: board.title,
    content: board.content,
    tag: board.tag,
    startAt: board.schedule_board_detail.start_at,
    endAt: board.schedule_board_detail.end_at,
    importance: board.schedule_board_detail.importance,
  }
}

// Backend: GET /board/
// Response item 중 회의록 게시글은 아래 값을 가진다.
// {
//   id: number,
//   board_type: 3,
//   title: string,
//   content: string,
//   tag?: string | null,
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
    label: event.type === 'meeting' ? `회의 ${event.title}` : event.title,
  }
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
