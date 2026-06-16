"use client";

import { cn } from "../lib/cn";
import { useWorkspace } from "../lib/store";
import type { CenterTab } from "../lib/types";
import { ChatView } from "./chat-view";
import { Icon } from "./icon";
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
        className="flex h-11 shrink-0 items-center gap-1 border-b border-border px-3"
      >
        {/* 토글: 높이/패딩/폰트를 줄여 더 콤팩트하게(11~12px). */}
        <div className="flex items-center gap-0.5 rounded-full bg-secondary p-0.5">
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
                "interactive rounded-full px-2.5 py-0.5 text-[11px]",
                tab === t
                  ? "bg-card font-semibold text-foreground shadow-elev-1"
                  : "font-medium text-muted-foreground hover:text-foreground",
              )}
            >
              {t === "대화" ? (
                <span className="flex items-center gap-1">
                  <Icon name="chat_bubble_outline" size={13} /> {t}
                </span>
              ) : (
                <span className="flex items-center gap-1">
                  <Icon name="description" size={13} /> {t}
                </span>
              )}
            </button>
          ))}
        </div>
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
