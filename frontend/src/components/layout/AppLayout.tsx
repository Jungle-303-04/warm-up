// 전체 화면 배치를 담당한다.

// AppLayout
// ├─ Sidebar
// └─ Main
//    ├─ Topbar
//    └─ Content

//AppLayout은 로그인 후 화면에서 반복되는 
// "사이드바 + 상단바 + 본문" 구조를 재사용하려고 만든 공통 레이아웃 컴포넌트입니다.


import type {ReactNode} from "react";
import { Sidebar } from "./Sidebar";

// 로그인 이후 화면의 공통 배치를 담당합니다.
// 왼쪽에는 Sidebar를 고정하고, 오른쪽에는 Topbar와 실제 페이지 내용을 배치합니다.
type AppLayoutProps = {
    topbar: ReactNode;
    children: ReactNode;
};

export function AppLayout ({topbar, children}: AppLayoutProps) {
    return (
        <div className="app-shell">
            {/* 모든 인증 후 화면에서 공통으로 보이는 왼쪽 메뉴입니다. */}
            <Sidebar />

            <div className="app-main">
                {/* CalendarPage가 넘겨준 상단바입니다. */}
                {topbar}
                {/* 각 페이지의 실제 본문이 들어가는 영역입니다. */}
                <main className="app-content">{children}</main>
            </div>
        </div>
    );
}
