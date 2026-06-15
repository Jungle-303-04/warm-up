"use client";

import { STUDIO_NOTES, STUDIO_TILES } from "../lib/fixtures";
import { Icon } from "./icon";

export function StudioPanel() {
  return (
    <aside className="flex w-[300px] shrink-0 flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
      <div className="flex items-center justify-between px-3 pt-3">
        <h2 className="text-[14px] font-semibold">스튜디오</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-3">
        <div className="grid grid-cols-3 gap-2">
          {STUDIO_TILES.map((t) => (
            <button
              key={t.label}
              type="button"
              disabled
              title={`${t.label} · 준비 중`}
              className="flex flex-col items-center gap-1.5 rounded-xl border border-border bg-secondary/40 px-2 py-3 text-center transition-colors hover:border-primary hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:border-border disabled:hover:bg-secondary/40"
            >
              <Icon name={t.icon} size={20} className="text-primary" />
              <span className="text-[11px] font-medium leading-tight">{t.label}</span>
            </button>
          ))}
        </div>

        <div className="mt-5 flex items-center justify-between">
          <p className="text-[13px] font-semibold">메모</p>
          <button
            type="button"
            disabled
            title="메모 추가 · 준비 중"
            className="inline-flex items-center gap-1 rounded-full border border-border px-2.5 py-1 text-[12px] text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-transparent"
          >
            <Icon name="add" size={16} /> 추가
          </button>
        </div>
        <div className="mt-2 space-y-2">
          {STUDIO_NOTES.map((n) => (
            <button
              key={n}
              type="button"
              disabled
              title={`${n} · 준비 중`}
              className="flex w-full items-center gap-2 rounded-xl border border-border bg-secondary/30 px-3 py-2.5 text-left text-[13px] transition-colors hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-secondary/30"
            >
              <Icon name="article" size={18} className="text-muted-foreground" />
              <span className="flex-1 truncate">{n}</span>
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}
