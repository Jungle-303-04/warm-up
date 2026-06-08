import { useMemo } from "react";
import { AppLayout } from "../components/layout/AppLayout";
import { Topbar } from "../components/layout/Topbar";

type CalendarDay = {
  date: Date;
  dayNumber: number;
  isCurrentMonth: boolean;
  isToday: boolean;
};

const WEEK_DAYS = ["월", "화", "수", "목", "금", "토", "일"];

function buildCalendarDays(baseDate: Date): CalendarDay[] {
  const year = baseDate.getFullYear();
  const month = baseDate.getMonth();

  const firstDayOfMonth = new Date(year, month, 1);
  const lastDayOfMonth = new Date(year, month + 1, 0);

  const firstDayWeekIndex = (firstDayOfMonth.getDay() + 6) % 7;
  const totalDaysInMonth = lastDayOfMonth.getDate();

  const days: CalendarDay[] = [];
  const today = new Date();

  for (let i = firstDayWeekIndex - 1; i >= 0; i -= 1) {
    const date = new Date(year, month, -i);
    days.push({
      date,
      dayNumber: date.getDate(),
      isCurrentMonth: false,
      isToday: false,
    });
  }

  for (let day = 1; day <= totalDaysInMonth; day += 1) {
    const date = new Date(year, month, day);

    days.push({
      date,
      dayNumber: day,
      isCurrentMonth: true,
      isToday:
        date.getFullYear() === today.getFullYear() &&
        date.getMonth() === today.getMonth() &&
        date.getDate() === today.getDate(),
    });
  }

  while (days.length < 42) {
    const lastDate = days[days.length - 1].date;
    const nextDate = new Date(
      lastDate.getFullYear(),
      lastDate.getMonth(),
      lastDate.getDate() + 1
    );

    days.push({
      date: nextDate,
      dayNumber: nextDate.getDate(),
      isCurrentMonth: false,
      isToday: false,
    });
  }

  return days;
}

function formatMonthLabel(date: Date) {
  return `${date.getFullYear()}년 ${date.getMonth() + 1}월`;
}

function isSameDate(date: Date, year: number, month: number, day: number) {
  return (
    date.getFullYear() === year &&
    date.getMonth() === month &&
    date.getDate() === day
  );
}

export function CalendarPage() {
  const currentDate = new Date();
  const currentMonthLabel = formatMonthLabel(currentDate);

  const calendarDays = useMemo(() => {
    return buildCalendarDays(currentDate);
  }, [currentDate]);

  const handleCreateMeeting = () => {
    alert("회의 작성 모달은 다음 단계에서 연결합니다.");
  };

  const handleCreateRetrospective = () => {
    alert("회고 작성 모달은 다음 단계에서 연결합니다.");
  };

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  return (
    <AppLayout
      topbar={
        <Topbar
          currentMonthLabel={currentMonthLabel}
          onCreateMeeting={handleCreateMeeting}
          onCreateRetrospective={handleCreateRetrospective}
        />
      }
    >
      <section className="calendar-card">
        <div className="calendar-week-header">
          {WEEK_DAYS.map((day) => (
            <div key={day} className="calendar-week-day">
              {day}
            </div>
          ))}
        </div>

        <div className="calendar-grid">
          {calendarDays.map((day) => {
            const hasSampleMeeting = isSameDate(day.date, year, month, 7);
            const hasSampleRetrospective = isSameDate(day.date, year, month, 7);

            return (
              <button
                key={day.date.toISOString()}
                type="button"
                className={[
                  "calendar-cell",
                  !day.isCurrentMonth ? "muted" : "",
                  day.isToday ? "today" : "",
                ].join(" ")}
              >
                <div className="calendar-cell-header">
                  <span>{day.dayNumber}</span>
                </div>

                <div className="calendar-events">
                  {hasSampleMeeting && (
                    <span className="calendar-event meeting">회의</span>
                  )}

                  {hasSampleRetrospective && (
                    <span className="calendar-event retrospective">회고</span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </section>
    </AppLayout>
  );
}