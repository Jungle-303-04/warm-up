import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import interactionPlugin from "@fullcalendar/interaction";
import type { EventClickArg, EventContentArg } from "@fullcalendar/core";
import type { DateClickArg } from "@fullcalendar/interaction";
import { useCallback, useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import { AppLayout } from "../components/layout/AppLayout";
import { Topbar } from "../components/layout/Topbar";
import { PageEditorModal } from "../components/modal/PageEditorModal";
import type { CalendarPageItem, PageType } from "../types/page";


//흐름

// 1. 오늘 날짜를 기본 선택 날짜로 잡음
// 2. 현재 년/월 상태를 만듦
// 3. 그 년/월로 백엔드에서 회의/회고 목록을 가져옴
// 4. 가져온 데이터를 캘린더 이벤트 형태로 바꿈
// 5. 선택한 날짜의 항목만 오른쪽 패널에 보여줌
// 6. 회의/회고 만들기 버튼을 누르면 작성 모달을 엶
// 7. 날짜나 이벤트를 클릭하면 선택 날짜나 상세 정보를 처리함




type CalendarPageProps = {
  onLogout: () => void;
};

// Date 객체를 백엔드와 FullCalendar에서 쓰는 YYYY-MM-DD 문자열로 바꿉니다.
function toDateKey(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

// 오른쪽 날짜 상세 패널에 보여줄 날짜 라벨을 만듭니다.
function formatKoreanDate(dateKey: string) {
  const date = new Date(`${dateKey}T00:00:00`);
  const dayNames = ["일", "월", "화", "수", "목", "금", "토"];

  return `${date.getFullYear()}년 ${
    date.getMonth() + 1
  }월 ${date.getDate()}일 (${dayNames[date.getDay()]})`;
}

// 페이지 타입을 캘린더에 표시할 짧은 라벨로 변환합니다.
function getTypeLabel(type: PageType) {
  return type === "MEETING" ? "회의" : "회고";
}

// 회의/회고마다 다른 색상을 적용하기 위한 CSS class를 고릅니다.
function getEventClassName(type: PageType) {
  return type === "MEETING" ? "teamlog-event-meeting" : "teamlog-event-retro";
}

//캘린더페이지 화면 만드는 함수
export function CalendarPage({ onLogout }: CalendarPageProps) {
  const todayKey = toDateKey(new Date());

  // 현재 FullCalendar가 보여주는 년/월입니다. 이 값으로 월별 API를 호출합니다.
  const [visibleYear, setVisibleYear] = useState(new Date().getFullYear());
  const [visibleMonth, setVisibleMonth] = useState(new Date().getMonth() + 1);
  
  // 사용자가 클릭한 날짜입니다. 오른쪽 상세 패널의 기준 날짜가 됩니다.
  const [selectedDate, setSelectedDate] = useState(todayKey);
  
  
  // 백엔드에서 받아온 월별 회의/회고 목록입니다.
  const [calendarItems, setCalendarItems] = useState<CalendarPageItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);


  // 값이 있으면 작성 모달이 열리고, 값은 작성할 페이지 타입이 됩니다.
  const [activeModalType, setActiveModalType] = useState<PageType | null>(null);

  const currentMonthLabel = `${visibleYear}년 ${visibleMonth}월`;

  const fetchCalendarItems = useCallback(async () => {
    try {
      setIsLoading(true);

      // 현재 보고 있는 년/월의 페이지 목록만 백엔드에서 가져옵니다.
      const response = await api.get<CalendarPageItem[]>("/pages/calendar", {
        params: {
          year: visibleYear,
          month: visibleMonth,
        },
      });

      setCalendarItems(response.data);
    } catch (error) {
      console.error(error);
      alert("캘린더 데이터를 불러오지 못했습니다.");
    } finally {
      setIsLoading(false);
    }
  }, [visibleYear, visibleMonth]);

  useEffect(() => {
    // 캘린더의 년/월이 바뀔 때마다 해당 월 데이터를 다시 조회합니다.
    fetchCalendarItems();
  }, [fetchCalendarItems]);

  const calendarEvents = useMemo(() => {
    // 백엔드 페이지 목록을 FullCalendar가 이해하는 이벤트 객체로 변환합니다.
    return calendarItems.map((item) => {
      return {
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
      };
    });
  }, [calendarItems]);

  const selectedDateItems = useMemo(() => {
    // 오른쪽 패널에는 선택한 날짜의 항목만 시간순으로 보여줍니다.
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
    // 상단바의 회의 만들기 버튼을 누르면 회의 작성 모달을 엽니다.
    setActiveModalType("MEETING");
  };

  const handleCreateRetrospective = () => {
    // 상단바의 회고 만들기 버튼을 누르면 회고 작성 모달을 엽니다.
    setActiveModalType("RETROSPECTIVE");
  };

  const handleDateClick = (arg: DateClickArg) => {
    // 캘린더 날짜를 클릭하면 오른쪽 상세 패널의 기준 날짜를 바꿉니다.
    setSelectedDate(arg.dateStr);
  };

  const handleEventClick = (arg: EventClickArg) => {
    // 현재는 상세 모달 대신 page_id를 alert로 확인하는 임시 흐름입니다.
    const date = arg.event.extendedProps.date as string;
    const pageId = arg.event.extendedProps.pageId as number;
    const pageTitle = arg.event.extendedProps.pageTitle as string;

    setSelectedDate(date);

    alert(`다음 단계에서 상세 모달을 엽니다.\npage_id=${pageId}\n${pageTitle}`);
  };

  const renderEventContent = (eventInfo: EventContentArg) => {
    // FullCalendar 기본 이벤트 UI 대신 회의/회고 라벨만 간단히 렌더링합니다.
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
          onLogout={onLogout}
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
              // 사용자가 이전/다음 달로 이동하면 visibleYear/Month를 갱신합니다.
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
                    alert(
                      `다음 단계에서 회의 상세 모달을 엽니다.\npage_id=${item.id}`
                    );
                  }}
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
                    alert(
                      `다음 단계에서 회고 상세 모달을 엽니다.\npage_id=${item.id}`
                    );
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

      {activeModalType !== null && (
        <PageEditorModal
          pageType={activeModalType}
          initialDate={selectedDate}
          onClose={() => setActiveModalType(null)}
          onSaved={() => {
            // 저장이 끝나면 모달을 닫고 월별 캘린더 데이터를 다시 불러옵니다.
            setActiveModalType(null);
            fetchCalendarItems();
          }}
        />
      )}
    </AppLayout>
  );
}
