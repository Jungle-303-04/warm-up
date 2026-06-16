"use client";

import { STUDIO_NOTES, STUDIO_TILES } from "../lib/fixtures";
import { Icon } from "./icon";
import { Panel } from "./ui/panel";

// 우 패널. 너비는 workspace 에서 style 로 주입(동적 리사이즈).
export function StudioPanel({ style }: { style?: React.CSSProperties }) {
  return (
    <Panel as="aside" className="shrink-0" style={style}>
      <div className="flex items-center justify-between px-4 pt-4 pb-1">
        <h2 className="text-[15px] font-semibold tracking-tight">스튜디오</h2>
        <span className="rounded-full bg-secondary px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
          준비 중
        </span>
      </div>

      <div className="scroll-thin flex-1 overflow-y-auto px-4 pb-4 pt-2">
        {/* 기능 카드 2열 그리드: 색조 아이콘 박스 + 라벨 + 보조설명 + chevron + 베타 배지 */}
        <div className="grid grid-cols-2 gap-2.5">
          {STUDIO_TILES.map((t) => (
            <button
              key={t.label}
              type="button"
              disabled
              title={`${t.label} · 준비 중`}
              className="interactive group relative flex flex-col gap-2.5 rounded-2xl border border-border bg-card p-3 text-left hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-elev-2 disabled:cursor-not-allowed"
            >
              {t.beta ? (
                <span className="absolute right-2 top-2 rounded-full bg-secondary px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-muted-foreground">
                  베타
                </span>
              ) : null}
              <span className={`studio-tint studio-tint-${t.tint} grid h-9 w-9 place-items-center rounded-xl`}>
                <Icon name={t.icon} size={18} />
              </span>
              <span className="min-w-0">
                <span className="flex items-center justify-between gap-1">
                  <span className="truncate text-[13px] font-medium leading-tight">{t.label}</span>
                  <Icon
                    name="chevron_right"
                    size={15}
                    className="shrink-0 text-muted-foreground/50 transition-transform group-hover:translate-x-0.5 group-hover:text-primary"
                  />
                </span>
                <span className="mt-0.5 block truncate text-[11px] text-muted-foreground">
                  {t.hint}
                </span>
              </span>
            </button>
          ))}
        </div>

        {/* 메모 섹션 */}
        <div className="mt-6 flex items-center justify-between">
          <p className="text-[13px] font-semibold">메모</p>
          <button
            type="button"
            disabled
            title="메모 추가 · 준비 중"
            className="interactive inline-flex items-center gap-1 rounded-full border border-border px-3 py-1.5 text-[12px] font-medium text-muted-foreground hover:bg-secondary hover:text-foreground disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:bg-transparent disabled:hover:text-muted-foreground"
          >
            <Icon name="add" size={15} /> 추가
          </button>
        </div>

        <div className="mt-2.5 space-y-2">
          {STUDIO_NOTES.map((n) => (
            <button
              key={n.title}
              type="button"
              disabled
              title={`${n.title} · 준비 중`}
              className="interactive flex w-full items-center gap-2.5 rounded-xl border border-border bg-card px-3 py-2.5 text-left disabled:cursor-not-allowed"
            >
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-secondary text-muted-foreground">
                <Icon name={n.icon} size={16} />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-[13px] font-medium leading-tight">
                  {n.title}
                </span>
                <span className="mt-0.5 flex items-center gap-1 text-[11px] text-muted-foreground">
                  <span>{n.kind}</span>
                  <span aria-hidden>·</span>
                  <span>{n.time}</span>
                </span>
              </span>
            </button>
          ))}

          {/* 메모 추가 placeholder(점선 카드) */}
          <button
            type="button"
            disabled
            title="메모 추가 · 준비 중"
            className="interactive flex w-full items-center justify-center gap-1.5 rounded-xl border border-dashed border-border px-3 py-2.5 text-[12.5px] text-muted-foreground hover:bg-secondary disabled:cursor-not-allowed disabled:hover:bg-transparent"
          >
            <Icon name="note_add" size={16} /> 새 메모
          </button>
        </div>
      </div>
    </Panel>
  );
}
