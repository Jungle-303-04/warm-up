"use client";

import { SOURCES, THREADS } from "../lib/fixtures";
import { useWorkspace } from "../lib/store";
import { Icon } from "./icon";
import { Checkbox, SourceRow } from "./source-row";

// 아직 백엔드 미연동인 액션은 비활성 + "준비 중"으로 명시(사일런트 데드엔드 제거).
function HeaderIcon({ name, label }: { name: string; label: string }) {
  return (
    <button
      type="button"
      disabled
      title={`${label} · 준비 중`}
      aria-label={`${label} · 준비 중`}
      className="grid h-8 w-8 place-items-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent"
    >
      <Icon name={name} size={18} />
    </button>
  );
}

export function SourcesPanel() {
  const selected = useWorkspace((s) => s.selected);
  const setAllSources = useWorkspace((s) => s.setAllSources);
  const activeThreadId = useWorkspace((s) => s.activeThreadId);
  const openThread = useWorkspace((s) => s.openThread);
  const newThread = useWorkspace((s) => s.newThread);
  const allOn = SOURCES.every((s) => selected[s.id]);

  return (
    <aside className="flex w-[320px] shrink-0 flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
      <div className="flex items-center justify-between px-3 pt-3">
        <h2 className="text-[14px] font-semibold">소스</h2>
        <div className="flex items-center">
          <HeaderIcon name="add" label="소스 추가" />
          <HeaderIcon name="travel_explore" label="탐색" />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-2 pt-1.5">
        <button
          type="button"
          aria-pressed={allOn}
          onClick={() => setAllSources(!allOn)}
          className="flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-[12px] text-muted-foreground transition-colors hover:bg-secondary"
        >
          모든 소스 선택
          <Checkbox checked={allOn} />
        </button>
        <div className="mt-1 space-y-0.5">
          {SOURCES.map((s) => (
            <SourceRow key={s.id} source={s} />
          ))}
        </div>

        <div className="mt-3 px-2">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            대화
          </p>
        </div>
        <div className="mt-1 space-y-0.5">
          {THREADS.map((t) => {
            const active = activeThreadId === t;
            return (
              <button
                key={t}
                type="button"
                onClick={() => openThread(t)}
                aria-current={active ? "true" : undefined}
                className={`flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-[13px] transition-colors ${
                  active ? "bg-secondary font-medium" : "hover:bg-secondary"
                }`}
              >
                <Icon name="chat_bubble_outline" size={16} className="text-muted-foreground" />
                <span className="flex-1 truncate">{t}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="border-t border-border p-3">
        <button
          type="button"
          onClick={newThread}
          className="flex w-full items-center justify-center gap-1.5 rounded-full border border-border py-2 text-[13px] text-foreground transition-colors hover:bg-secondary"
        >
          <Icon name="add" size={18} /> 새 대화
        </button>
      </div>
    </aside>
  );
}
