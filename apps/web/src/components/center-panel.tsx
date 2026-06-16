"use client";

import { cn } from "../lib/cn";
import { useWorkspace } from "../lib/store";
import type { CenterTab } from "../lib/types";
import { ChatView } from "./chat-view";
import { Panel } from "./ui/panel";
import { ViewerPanel } from "./viewer-panel";

const TABS: CenterTab[] = ["대화", "뷰어"];

// 중앙 패널: 채팅 ⇄ 뷰어 토글.
export function CenterPanel() {
  const tab = useWorkspace((s) => s.centerTab);
  const setTab = useWorkspace((s) => s.setCenterTab);
  return (
    <Panel className="flex-1">
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
            className={cn(
              "rounded-full px-2.5 py-1 text-[13px] transition-colors",
              tab === t
                ? "bg-secondary font-semibold text-foreground"
                : "text-muted-foreground hover:text-foreground",
            )}
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
        {tab === "대화" ? <ChatView /> : <ViewerPanel />}
      </div>
    </Panel>
  );
}
