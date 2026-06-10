// 왼쪽 사이드바
// └─ 캘린더

import { CalendarDays } from "lucide-react";

// 앱 왼쪽에 고정되는 사이드바입니다. 현재는 캘린더 메뉴만 있습니다.
export function Sidebar() {
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
                <button className="sidebar-nav-item active">
                    <CalendarDays size={18} />
                    <span>캘린더</span>
                </button>
            </nav>
        </aside>
    );
}
