import { CalendarDays, MessageSquareText, Search } from "lucide-react";

import type { AppPage } from "./AppLayout";

type SidebarProps = {
  activePage: AppPage;
  onNavigate: (page: AppPage) => void;
};

export function Sidebar({ activePage, onNavigate }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">T</div>
        <div>
          <div className="sidebar-logo-title">TeamLog</div>
          <div className="sidebar-logo-subtitle">협업 기록 도구</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {/* 캘린더 메뉴를 누르면 App.tsx가 CalendarPage를 렌더링한다. */}
        <button
          className={`sidebar-nav-item ${
            activePage === "calendar" ? "active" : ""
          }`}
          type="button"
          onClick={() => onNavigate("calendar")}
        >
          <CalendarDays size={18} />
          <span>캘린더</span>
        </button>

        {/* 오늘의 한마디 메뉴를 누르면 App.tsx가 DailyMessagePage를 렌더링한다. */}
        <button
          className={`sidebar-nav-item ${
            activePage === "daily-message" ? "active" : ""
          }`}
          type="button"
          onClick={() => onNavigate("daily-message")}
        >
          <MessageSquareText size={18} />
          <span>오늘의 한마디</span>
        </button>
        <button
          className={`sidebar-nav-item ${
            activePage === "search" ? "active" : ""
          }`}
          type="button"
          onClick={() => onNavigate("search")}
        >
          <Search size={18} />
          <span>검색</span>
        </button>
      </nav>
    </aside>
  );
}
