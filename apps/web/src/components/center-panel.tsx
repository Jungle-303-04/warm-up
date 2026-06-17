"use client";

import { cn } from "../lib/cn";
import { selectScopeCount, useWorkspace } from "../lib/store";
import type { CenterTab } from "../lib/types";
import { ChatView } from "./chat-view";
import { Icon } from "./icon";
import { Button } from "./ui/button";
import { Panel } from "./ui/panel";
import { ViewerPanel } from "./viewer-panel";

const TABS: CenterTab[] = ["대화", "뷰어"];

// 중앙 패널: 채팅 ⇄ 뷰어 토글.
export function CenterPanel() {
  const tab = useWorkspace((s) => s.centerTab);
  const setTab = useWorkspace((s) => s.setCenterTab);
  // 대화 컨트롤(기준 개수/메모저장/초기화)은 스크롤과 무관하게 항상 보이도록 탭 바 우측에 둠
  const scopeCount = useWorkspace(selectScopeCount);
  const chatMessageCount = useWorkspace((s) => s.chatMessageCount);
  const requestResetChat = useWorkspace((s) => s.requestResetChat);
  const requestSaveChat = useWorkspace((s) => s.requestSaveChat);
  const hasChat = chatMessageCount > 0;
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
                "transition-all duration-200 ease-in-out rounded-full px-2.5 py-0.5 text-[11px]",
                tab === t
                  ? "bg-card font-semibold text-foreground shadow-sm"
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

        {/* 대화 컨트롤: 기준 개수 배지 + 메모로 저장 + 초기화. 대화 탭에서만 노출. */}
        {tab === "대화" ? (
          <div className="ml-auto flex items-center gap-1.5">
            <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-accent/60 px-2.5 py-0.5 text-[11px] font-medium text-accent-foreground">
              <Icon name="check_circle" size={12.5} />
              {scopeCount}개 기준
            </span>
            <Button
              variant="outline"
              size="xs"
              icon="save_note"
              onClick={requestSaveChat}
              disabled={!hasChat}
              title="대화를 메모로 저장"
              aria-label="대화를 메모로 저장"
            >
              메모 저장
            </Button>
            <Button
              variant="outline"
              size="xs"
              icon="delete"
              onClick={requestResetChat}
              disabled={!hasChat}
              title="대화 초기화"
              aria-label="대화 초기화"
            >
              초기화
            </Button>
          </div>
        ) : null}
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
