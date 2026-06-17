import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import interactionPlugin from "@fullcalendar/interaction";
import { Pencil } from "lucide-react";
import type { EventClickArg, EventContentArg } from "@fullcalendar/core";
import type { DateClickArg } from "@fullcalendar/interaction";
import { useCallback, useMemo, useRef, useState } from "react";

import { api } from "../api/client";
import { AppLayout } from "../components/layout/AppLayout";
import type { AppPage } from "../components/layout/AppLayout";
import { Topbar } from "../components/layout/Topbar";
import { PageDetailModal } from "../components/modal/PageDetailModal";
import { PageEditorModal } from "../components/modal/PageEditorModal";
import type { UserResponse } from "../api/auth";
import type { CalendarPageItem, PageType } from "../types/page";

type CalendarPageProps = {
  currentUser: UserResponse | null;
  onLogout: () => void;
  onNavigate: (page: AppPage) => void;
};

function toDateKey(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

function formatKoreanDate(dateKey: string) {
  const date = new Date(`${dateKey}T00:00:00`);
  const dayNames = ["일", "월", "화", "수", "목", "금", "토"];

  return `${date.getFullYear()}년 ${
    date.getMonth() + 1
  }월 ${date.getDate()}일 (${dayNames[date.getDay()]})`;
}

function getTypeLabel(type: PageType) {
  return type === "MEETING" ? "회의" : "회고";
}

function getEventClassName(type: PageType) {
  return type === "MEETING" ? "teamlog-event-meeting" : "teamlog-event-retro";
}

export function CalendarPage({
  currentUser,
  onLogout,
  onNavigate,
}: CalendarPageProps) {
  const todayKey = toDateKey(new Date());
  const calendarRef = useRef<FullCalendar | null>(null);

  const [visibleYear, setVisibleYear] = useState(new Date().getFullYear());
  const [visibleMonth, setVisibleMonth] = useState(new Date().getMonth() + 1);
  const [selectedDate, setSelectedDate] = useState(todayKey);
  const [calendarItems, setCalendarItems] = useState<CalendarPageItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeModalType, setActiveModalType] = useState<PageType | null>(null);
  const [selectedPageId, setSelectedPageId] = useState<number | null>(null);

  const currentMonthLabel = `${visibleYear}년 ${visibleMonth}월`;
  const isSelectedDateToday = selectedDate === todayKey;
  const todayOnlyMessage = "오늘 날짜에만 회의나 회고를 작성할 수 있습니다.";

  const fetchCalendarItems = useCallback(
    async (year = visibleYear, month = visibleMonth) => {
      try {
        setIsLoading(true);

        const response = await api.get<CalendarPageItem[]>("/pages/calendar", {
          params: {
            year,
            month,
          },
        });

        setCalendarItems(response.data);
      } catch (error) {
        console.error(error);
        alert("캘린더 데이터를 불러오지 못했습니다.");
      } finally {
        setIsLoading(false);
      }
    },
    [visibleYear, visibleMonth]
  );

  const calendarEvents = useMemo(() => {
    return calendarItems.map((item) => ({
      id: String(item.id),
      title: getTypeLabel(item.type),
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
    }));
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

  const canEditItem = (item: CalendarPageItem) => {
    return currentUser?.id === item.author_id;
  };

  const handleCreateMeeting = () => {
    if (!isSelectedDateToday) {
      alert(todayOnlyMessage);
      return;
    }

    setActiveModalType("MEETING");
  };

  const handleCreateRetrospective = () => {
    if (!isSelectedDateToday) {
      alert(todayOnlyMessage);
      return;
    }

    setActiveModalType("RETROSPECTIVE");
  };

  const handleDateClick = (arg: DateClickArg) => {
    setSelectedDate(arg.dateStr);
  };

  const handleEventClick = (arg: EventClickArg) => {
    const date = arg.event.extendedProps.date as string;

    setSelectedDate(date);
  };

  const handleOpenPageDetail = (pageId: number) => {
    setSelectedPageId(pageId);
  };

  const handleTodayClick = () => {
    calendarRef.current?.getApi().today();
    setSelectedDate(todayKey);
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
      activePage="calendar"
      onNavigate={onNavigate}
      topbar={
        <Topbar
          currentMonthLabel={currentMonthLabel}
          onCreateMeeting={handleCreateMeeting}
          onCreateRetrospective={handleCreateRetrospective}
          onLogout={onLogout}
          currentUser={currentUser}
          canCreatePage={isSelectedDateToday}
          createDisabledMessage={todayOnlyMessage}
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
                  : "날짜 칸을 클릭하면 오른쪽 패널에서 회의와 회고를 볼 수 있습니다."}
              </p>
            </div>
          </div>

          <FullCalendar
            ref={calendarRef}
            plugins={[dayGridPlugin, interactionPlugin]}
            initialView="dayGridMonth"
            locale="ko"
            height="auto"
            customButtons={{
              todayWithPanel: {
                text: "오늘",
                click: handleTodayClick,
              },
            }}
            headerToolbar={{
              left: "prev,next todayWithPanel",
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
              const year = currentStart.getFullYear();
              const month = currentStart.getMonth() + 1;

              setVisibleYear(year);
              setVisibleMonth(month);
              fetchCalendarItems(year, month);
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
                  onClick={() => handleOpenPageDetail(item.id)}
                >
                  <div>
                    <strong>{item.title}</strong>
                    <p>
                      {item.start_time
                        ? `${item.start_time.slice(0, 5)}${
                            item.end_time
                              ? ` - ${item.end_time.slice(0, 5)}`
                              : ""
                          }`
                        : "시간 없음"}
                    </p>
                  </div>
                  <span className="detail-item-action">
                    {canEditItem(item) ? <Pencil size={16} /> : <>&rsaquo;</>}
                  </span>
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
                  onClick={() => handleOpenPageDetail(item.id)}
                >
                  <div>
                    <strong>{item.title}</strong>
                    <p>팀 회고</p>
                  </div>
                  <span className="detail-item-action">
                    {canEditItem(item) ? <Pencil size={16} /> : <>&rsaquo;</>}
                  </span>
                </button>
              ))}

            {retrospectiveCount === 0 && (
              <p className="empty-detail-text">등록된 회고가 없습니다.</p>
            )}
          </div>
        </aside>
      </div>

      {activeModalType !== null && (
        <PageEditorModal
          pageType={activeModalType}
          initialDate={todayKey}
          onClose={() => setActiveModalType(null)}
          onSaved={() => {
            setActiveModalType(null);
            fetchCalendarItems();
          }}
        />
      )}

      {selectedPageId !== null && (
        <PageDetailModal
          pageId={selectedPageId}
          currentUser={currentUser}
          onClose={() => setSelectedPageId(null)}
          onSaved={() => {
            setSelectedPageId(null);
            fetchCalendarItems();
          }}
        />
      )}
    </AppLayout>
  );
}
