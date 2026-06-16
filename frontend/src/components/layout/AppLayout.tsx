import type { ReactNode } from "react";

import { ChatbotWidget } from "../chatbot/ChatbotWidget";
import { Sidebar } from "./Sidebar";

export type AppPage = "calendar" | "daily-message";

type AppLayoutProps = {
  topbar?: ReactNode;
  children: ReactNode;
  // 현재 선택된 사이드바 메뉴다.
  activePage: AppPage;
  // 사이드바 메뉴를 눌렀을 때 App.tsx의 activePage를 바꾸는 함수다.
  onNavigate: (page: AppPage) => void;
};

export function AppLayout({
  topbar,
  children,
  activePage,
  onNavigate,
}: AppLayoutProps) {
  return (
    <div className="app-shell">
      {/* 캘린더/오늘의 한마디 메뉴를 공통으로 보여주는 왼쪽 사이드바다. */}
      <Sidebar activePage={activePage} onNavigate={onNavigate} />

      <div className="app-main">
        {/* 각 페이지가 넘겨주는 상단바 영역이다. */}
        {topbar}
        {/* 실제 페이지 본문이 들어가는 영역이다. */}
        <main className="app-content">{children}</main>
      </div>

      <ChatbotWidget />
    </div>
  );
}
