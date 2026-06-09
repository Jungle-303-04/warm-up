import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import interactionPlugin from "@fullcalendar/interaction";
import type {
  DateClickArg,
  EventClickArg,
  EventContentArg,
} from "@fullcalendar/core";
import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import { AppLayout } from "../components/layout/AppLayout";
import { Topbar } from "../components/layout/Topbar";
import type { CalendarPageItem, PageType } from "../types/page";

function toDateKey(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

function formatKoreanDate(dateKey: string) {
  const date = new Date(`${dateKey}T00:00:00`);
  const dayNames = ["일", "월", "화", "수", "목", "금", "토"];

  return `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일 (${
    dayNames[date.getDay()]
  })`;
}

function getTypeLabel(type: PageType) {
  return type === "MEETING" ? "회의" : "회고";
}

function getEventClassName(type: PageType) {
  return type === "MEETING" ? "teamlog-event-meeting" : "teamlog-event-retro";
}

export function CalendarPage() {
  const todayKey = toDateKey(new Date());

  const [visibleYear, setVisibleYear] = useState(new Date().getFullYear());
  const [visibleMonth, setVisibleMonth] = useState(new Date().getMonth() + 1);
  const [selectedDate, setSelectedDate] = useState(todayKey);
  const [calendarItems, setCalendarItems] = useState<CalendarPageItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const currentMonthLabel = `${visibleYear}년 ${visibleMonth}월`;

  useEffect(() => {
    const fetchCalendarItems = async () => {
      try {
        setIsLoading(true);

        const response = await api.get<CalendarPageItem[]>("/pages/calendar", {
          params: {
            year: visibleYear,
            month: visibleMonth,
          },
        });

        setCalendarItems(response.data);
      } catch (error) {
        console.error(error);
        alert(
          "캘린더 데이터를 불러오지 못했습니다. 로그인 토큰이 있는지 확인해주세요."
        );
      } finally {
        setIsLoading(false);
      }
    };

    fetchCalendarItems();
  }, [visibleYear, visibleMonth]);

  const calendarEvents = useMemo(() => {
    return calendarItems.map((item) => {
      const title = getTypeLabel(item.type);

      return {
        id: String(item.id),
        title,
        start: item.start_time ? `${item.date}T${item.start_time}` : item.date,
        end: item.end_time ? `${item.date}T${item.end_time}` : undefined,
        allDay: item.start_time === null,
        classNames: [getEventClassName(item.type)],
        extendedProps: {
          pageId: item.id,
          pageType: item.type,
          pageTitle: item.title,
          date: item.date,
          startTime: item.start_time,
          endTime: item.end_time,
        },
      };
    });
  }, [calendarItems]);

  const selectedDateItems = useMemo(() => {
    return calendarItems
      .filter((item) => item.date === selectedDate)
      .sort((a, b) => {
        const aTime = a.start_time ?? "99:99:99";
        const bTime = b.start_time ?? "99:99:99";

        return aTime.localeCompare(bTime);
      });
  }, [calendarItems, selectedDate]);

  const meetingCount = selectedDateItems.filter(
    (item) => item.type === "MEETING"
  ).length;

  const retrospectiveCount = selectedDateItems.filter(
    (item) => item.type === "RETROSPECTIVE"
  ).length;

  const handleCreateMeeting = () => {
    alert("다음 단계에서 회의 작성 모달을 연결합니다.");
  };

  const handleCreateRetrospective = () => {
    alert("다음 단계에서 회고 작성 모달을 연결합니다.");
  };

  const handleDateClick = (arg: DateClickArg) => {
    setSelectedDate(arg.dateStr);
  };

  const handleEventClick = (arg: EventClickArg) => {
    const date = arg.event.extendedProps.date as string;
    const pageId = arg.event.extendedProps.pageId as number;
    const pageTitle = arg.event.extendedProps.pageTitle as string;

    setSelectedDate(date);

    alert(`다음 단계에서 상세 모달을 엽니다.\npage_id=${pageId}\n${pageTitle}`);
  };

  const renderEventContent = (eventInfo: EventContentArg) => {
    const pageType = eventInfo.event.extendedProps.pageType as PageType;

    return (
      <span className="teamlog-event-content">
        {pageType === "MEETING" ? "회의" : "회고"}
      </span>
    );
  };

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
      <div className="calendar-page-layout">
        <section className="calendar-card fullcalendar-card">
          <div className="calendar-card-header">
            <div>
              <h2>{currentMonthLabel}</h2>
              <p>
                {isLoading
                  ? "캘린더 데이터를 불러오는 중입니다."
                  : "날짜 칸의 회의/회고 태그를 클릭하면 상세를 볼 수 있습니다."}
              </p>
            </div>
          </div>

          <FullCalendar
            plugins={[dayGridPlugin, interactionPlugin]}
            initialView="dayGridMonth"
            locale="ko"
            height="auto"
            headerToolbar={{
              left: "prev,next today",
              center: "title",
              right: "",
            }}
            buttonText={{
              today: "오늘",
            }}
            dayMaxEvents={3}
            events={calendarEvents}
            datesSet={(arg) => {
              const currentStart = arg.view.currentStart;

              setVisibleYear(currentStart.getFullYear());
              setVisibleMonth(currentStart.getMonth() + 1);
            }}
            dateClick={handleDateClick}
            eventClick={handleEventClick}
            eventContent={renderEventContent}
          />
        </section>

        <aside className="day-detail-panel">
          <div className="day-detail-header">
            <div>
              <h2>{formatKoreanDate(selectedDate)}</h2>
              <p>선택한 날짜의 회의와 회고입니다.</p>
            </div>
          </div>

          <div className="day-summary">
            <div className="summary-chip meeting">회의 {meetingCount}</div>
            <div className="summary-chip retrospective">
              회고 {retrospectiveCount}
            </div>
          </div>

          <div className="detail-section">
            <div className="detail-section-title">
              <span>회의록</span>
              <span>{meetingCount}</span>
            </div>

            {selectedDateItems
              .filter((item) => item.type === "MEETING")
              .map((item) => (
                <button
                  key={item.id}
                  className="detail-item"
                  type="button"
                  onClick={() => {
                    alert(`다음 단계에서 회의 상세 모달을 엽니다.\npage_id=${item.id}`);
                  }}
                >
                  <div>
                    <strong>{item.title}</strong>
                    <p>
                      {item.start_time
                        ? `${item.start_time.slice(0, 5)}${
                            item.end_time ? ` - ${item.end_time.slice(0, 5)}` : ""
                          }`
                        : "시간 없음"}
                    </p>
                  </div>
                  <span>›</span>
                </button>
              ))}

            {meetingCount === 0 && (
              <p className="empty-detail-text">등록된 회의가 없습니다.</p>
            )}
          </div>

          <div className="detail-section">
            <div className="detail-section-title">
              <span>회고록</span>
              <span>{retrospectiveCount}</span>
            </div>

            {selectedDateItems
              .filter((item) => item.type === "RETROSPECTIVE")
              .map((item) => (
                <button
                  key={item.id}
                  className="detail-item"
                  type="button"
                  onClick={() => {
                    alert(`다음 단계에서 회고 상세 모달을 엽니다.\npage_id=${item.id}`);
                  }}
                >
                  <div>
                    <strong>{item.title}</strong>
                    <p>팀 회고</p>
                  </div>
                  <span>›</span>
                </button>
              ))}

            {retrospectiveCount === 0 && (
              <p className="empty-detail-text">등록된 회고가 없습니다.</p>
            )}
          </div>
        </aside>
      </div>
    </AppLayout>
  );
}