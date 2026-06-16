"use client";

import { cn } from "../lib/cn";
import { STUDIO_HERO, STUDIO_NOTES, STUDIO_TILES } from "../lib/fixtures";
import { useWorkspace } from "../lib/store";
import { Icon } from "./icon";
import { Panel } from "./ui/panel";

// 우 패널. 너비는 workspace 에서 style 로 주입(동적 리사이즈).
// 소스 0개면 전체를 살짝 dim 처리 + 안내(아직 비활성 톤).
export function StudioPanel({ style }: { style?: React.CSSProperties }) {
  const sourceCount = useWorkspace((s) => s.sources.length);
  const empty = sourceCount === 0;

  return (
    <Panel as="aside" className="shrink-0" style={style}>
      <div className="flex items-center justify-between px-4 pb-2 pt-4">
        <div className="flex items-center gap-2">
          <Icon name="auto_awesome" size={16} className="text-primary" />
          <h2 className="t-title">스튜디오</h2>
        </div>
        <span className="rounded-full bg-secondary px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
          준비 중
        </span>
      </div>

      <div className="scroll-thin relative flex-1 overflow-y-auto px-4 pb-4 pt-1.5">
        {/* 소스 0개일 때 비활성 안내 배너 */}
        {empty ? (
          <div className="mb-3 flex items-start gap-2 rounded-xl border border-dashed border-border bg-secondary/40 px-3 py-2.5 text-[12px] leading-snug text-muted-foreground">
            <Icon name="check_circle" size={14} className="mt-0.5 shrink-0" />
            <span>소스를 추가하면 스튜디오 산출물을 만들 수 있어요.</span>
          </div>
        ) : null}

        <div className={cn(empty && "pointer-events-none select-none opacity-55")}>
          {/* 와이드 히어로 카드: 가장 강조되는 산출물 */}
          <button
            type="button"
            disabled
            title={`${STUDIO_HERO.label} · 준비 중`}
            className="interactive group relative flex w-full items-center gap-3.5 overflow-hidden rounded-2xl border border-border bg-card p-4 text-left hover:border-primary/30 hover:shadow-elev-2 disabled:cursor-not-allowed"
          >
            <span
              className={`studio-tint studio-tint-${STUDIO_HERO.tint} grid h-12 w-12 shrink-0 place-items-center rounded-2xl`}
            >
              <Icon name={STUDIO_HERO.icon} size={24} />
            </span>
            <span className="min-w-0 flex-1">
              <span className="flex items-center gap-2">
                <span className="t-title truncate">{STUDIO_HERO.label}</span>
                <span className="rounded-full bg-secondary px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-muted-foreground">
                  베타
                </span>
              </span>
              <span className="mt-0.5 block truncate text-[12px] text-muted-foreground">
                {STUDIO_HERO.hint}
              </span>
            </span>
            <Icon
              name="chevron_right"
              size={18}
              className="shrink-0 text-muted-foreground/50 transition-transform group-hover:translate-x-0.5 group-hover:text-primary"
            />
          </button>

          {/* 기능 카드 2열 그리드: 채도 또렷한 색조 박스 + 라벨 위계 강화 */}
          <div className="mt-3 grid grid-cols-2 gap-2.5">
            {STUDIO_TILES.map((t) => (
              <button
                key={t.label}
                type="button"
                disabled
                title={`${t.label} · 준비 중`}
                className="interactive group relative flex min-h-[112px] flex-col gap-2.5 rounded-2xl border border-border bg-card p-3.5 text-left hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-elev-2 disabled:cursor-not-allowed"
              >
                {t.beta ? (
                  <span className="absolute right-2.5 top-2.5 rounded-full bg-secondary px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-muted-foreground">
                    베타
                  </span>
                ) : null}
                <span
                  className={`studio-tint studio-tint-${t.tint} grid h-10 w-10 place-items-center rounded-xl`}
                >
                  <Icon name={t.icon} size={20} />
                </span>
                <span className="min-w-0">
                  <span className="flex items-center justify-between gap-1">
                    <span className="truncate text-[13.5px] font-semibold leading-tight tracking-tight">
                      {t.label}
                    </span>
                    <Icon
                      name="chevron_right"
                      size={15}
                      className="shrink-0 text-muted-foreground/40 transition-transform group-hover:translate-x-0.5 group-hover:text-primary"
                    />
                  </span>
                  <span className="mt-1 block text-[11.5px] leading-snug text-muted-foreground">
                    {t.hint}
                  </span>
                </span>
              </button>
            ))}
          </div>

          {/* 메모 섹션 */}
          <div className="mt-6 flex items-center justify-between">
            <p className="t-section">메모</p>
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
                className="interactive flex w-full items-center gap-2.5 rounded-xl border border-border bg-card px-3 py-2.5 text-left hover:border-primary/30 hover:shadow-elev-1 disabled:cursor-not-allowed"
              >
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-secondary text-muted-foreground">
                  <Icon name={n.icon} size={17} />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-[13px] font-semibold leading-tight">
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
      </div>
    </Panel>
  );
}
