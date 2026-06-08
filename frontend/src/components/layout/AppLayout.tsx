// 전체 화면 배치를 담당한다.

// AppLayout
// ├─ Sidebar
// └─ Main
//    ├─ Topbar
//    └─ Content

import type {ReactNode} from "react";
import { Sidebar } from "./Sidebar";

type AppLayoutProps = {
    topbar: ReactNode;
    children: ReactNode;
};

export function AppLayout ({topbar, children}: AppLayoutProps) {
    return (
        <div className="app-shell">
            <Sidebar />

            <div className="app-main">
                {topbar}
                <main className="app-content">{children}</main>
            </div>
        </div>
    );
}