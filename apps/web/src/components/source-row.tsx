"use client";

import { SOURCE_KINDS } from "../lib/fixtures";
import { useWorkspace } from "../lib/store";
import type { Source } from "../lib/types";
import { Icon } from "./icon";

export function Checkbox({ checked }: { checked: boolean }) {
  return (
    <span
      aria-hidden
      className={`grid h-4 w-4 shrink-0 place-items-center rounded-[5px] border transition-colors ${
        checked
          ? "border-primary bg-primary text-primary-foreground"
          : "border-input text-transparent"
      }`}
    >
      <Icon name="check" size={11} strokeWidth={3} />
    </span>
  );
}

function ProgressBar({ value }: { value: number }) {
  return (
    <>
      <span aria-hidden>·</span>
      <span className="h-[3px] w-10 overflow-hidden rounded-full bg-border">
        <span
          className="block h-full rounded-full bg-primary"
          style={{ width: `${value}%` }}
        />
      </span>
      <span>{value}%</span>
    </>
  );
}

// 한 행에 두 개의 분리된 액션:
//  · 체크박스 버튼 = 범위 포함/제외 (대화 답변 범위)
//  · 본문 버튼     = 뷰어에서 열어 읽기
export function SourceRow({ source }: { source: Source }) {
  const checked = useWorkspace((s) => !!s.selected[source.id]);
  const focused = useWorkspace((s) => s.focusedSourceId === source.id);
  const toggleSource = useWorkspace((s) => s.toggleSource);
  const openSource = useWorkspace((s) => s.openSource);

  const cfg = SOURCE_KINDS[source.kind];
  const done = source.progress >= 100;

  return (
    <div
      className={`group flex items-center gap-1 rounded-lg pr-1 transition-colors ${
        focused ? "bg-secondary" : "hover:bg-secondary"
      }`}
    >
      <button
        type="button"
        onClick={() => toggleSource(source.id)}
        role="checkbox"
        aria-checked={checked}
        aria-label={`${source.name} 범위 ${checked ? "제외" : "포함"}`}
        className="grid h-8 w-8 shrink-0 place-items-center rounded-lg"
      >
        <Checkbox checked={checked} />
      </button>

      <button
        type="button"
        onClick={() => openSource(source.id)}
        aria-current={focused ? "true" : undefined}
        title={`${source.name} 열기`}
        className="flex min-w-0 flex-1 items-center gap-2.5 rounded-lg py-1.5 pr-1 text-left"
      >
        <span
          className="grid h-7 w-7 shrink-0 place-items-center rounded-md"
          style={{ background: cfg.chipBg, color: cfg.chipFg }}
        >
          <Icon name={cfg.icon} size={16} />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-[13px] leading-tight">{source.name}</span>
          <span className="mt-0.5 flex items-center gap-1 text-[11px] text-muted-foreground">
            <span>{cfg.label}</span>
            {source.kind === "repo" ? (
              <>
                <span aria-hidden>·</span>
                <span>모든 브랜치</span>
              </>
            ) : null}
            {done ? null : <ProgressBar value={source.progress} />}
          </span>
        </span>
      </button>
    </div>
  );
}
