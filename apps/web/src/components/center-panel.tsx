"use client";

import { useWorkspace } from "../lib/store";
import type { CenterTab } from "../lib/types";
import { BoardPanel } from "./board-panel";
import { ChatView } from "./chat-view";
import { ViewerPanel } from "./viewer-panel";

const TABS: CenterTab[] = ["대화", "보드", "뷰어"];

export function CenterPanel() {
  const tab = useWorkspace((s) => s.centerTab);
  const setTab = useWorkspace((s) => s.setCenterTab);
  return (
    <section className="flex flex-1 flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
      <div
        role="tablist"
        aria-label="중앙 패널 보기"
        className="flex h-12 shrink-0 items-center gap-1 border-b border-border px-3"
      >
        {TABS.map((t) => (
          <button
            key={t}
            role="tab"
            type="button"
            id={`tab-${t}`}
            aria-selected={tab === t}
            aria-controls={`panel-${t}`}
            onClick={() => setTab(t)}
            className={`rounded-full px-2.5 py-1 text-[13px] transition-colors ${
              tab === t
                ? "bg-secondary font-semibold text-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <div
        role="tabpanel"
        id={`panel-${tab}`}
        aria-labelledby={`tab-${tab}`}
        className="flex min-h-0 flex-1 flex-col"
      >
        {tab === "대화" ? <ChatView /> : tab === "보드" ? <BoardPanel /> : <ViewerPanel />}
      </div>
    </section>
  );
}
