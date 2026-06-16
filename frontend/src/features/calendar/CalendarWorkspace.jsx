const SCHEDULE_BOARD_TYPE = 2
const PROCEEDINGS_BOARD_TYPE = 3
const WEEKDAY_LABELS = ['일', '월', '화', '수', '목', '금', '토']

export function CalendarWorkspace({
  boards,
  selectedEvent,
  visibleMonth,
  isLoadingBoards,
  onPreviousMonth,
  onNextMonth,
  onCurrentMonth,
  onReloadBoards,
  onSelectEvent,
  onOpenBoard,
}) {
  const calendarEvents = boards.flatMap(mapBoardToCalendarEvents)
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

      <div className="calendar-legend" aria-label="캘린더 표시 구분">
        <span>
          <i className="legend-schedule" />
          일정
        </span>
        <span>
          <i className="legend-meeting" />
          회의록
        </span>
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
            onSelectEvent={onSelectEvent}
          />
        ))}
      </div>

      {monthEvents.length === 0 ? (
        <p className="calendar-empty">
          이번 달에 표시할 일정형 게시글이나 회의록 게시글이 없습니다.
        </p>
      ) : null}

      <CalendarEventDetail
        selectedEvent={selectedEvent}
        onOpenBoard={onOpenBoard}
      />
    </section>
  )
}

function CalendarWeek({ week, segments, visibleMonth, onSelectEvent }) {
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
            onClick={() => onSelectEvent(segment.event)}
          >
            {segment.label}
          </button>
        ))}
      </div>
    </div>
  )
}

function CalendarEventDetail({ selectedEvent, onOpenBoard }) {
  if (!selectedEvent) {
    return (
      <aside className="calendar-detail" aria-label="선택한 게시글">
        <strong>선택한 게시글 없음</strong>
        <p>일정이나 회의록 게시글 정보가 여기에 표시됩니다.</p>
      </aside>
    )
  }

  return (
    <aside className="calendar-detail" aria-label="선택한 게시글">
      <div className="calendar-detail-header">
        <span>{selectedEvent.type === 'schedule' ? '일정' : '회의록'}</span>
        <strong>{selectedEvent.title}</strong>
      </div>
      <dl>
        <div>
          <dt>게시글 ID</dt>
          <dd>{selectedEvent.boardId}</dd>
        </div>
        <div>
          <dt>기간</dt>
          <dd>{formatEventRange(selectedEvent)}</dd>
        </div>
        <div>
          <dt>태그</dt>
          <dd>{selectedEvent.tag || '-'}</dd>
        </div>
      </dl>
      <p>{selectedEvent.content}</p>
      <button
        type="button"
        className="calendar-open-button"
        onClick={() => onOpenBoard(selectedEvent.boardId)}
      >
        게시글 상세 불러오기
      </button>
    </aside>
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

// Backend: GET /board/
// Response item 중 일정 게시글은 아래 값을 가진다.
// {
//   id: number,
//   board_type: 2,
//   title: string,
//   content: string,
//   tag?: string | null,
//   schedule_board_detail: {
//     start_at: string,
//     end_at: string,
//     importance: number
//   }
// }
// 화면에서는 start_at부터 end_at까지 이어지는 일정 막대로 표시한다.
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
//   proceedings_board_detail: {
//     meeting_date: string
//   }
// }
// 화면에서는 meeting_date 하루에 회의록 이벤트로 표시한다.
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

function formatEventRange(event) {
  const start = toDateKey(new Date(event.startAt))
  const end = toDateKey(new Date(event.endAt))
  return start === end ? start : `${start} ~ ${end}`
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
