"use client";

import { cn } from "../lib/cn";
import type { IndexProgress } from "../lib/types";

const STAGES = ["queued", "running", "done"] as const;
const STAGE_LABELS: Record<(typeof STAGES)[number], string> = {
  queued: "대기",
  running: "분석",
  done: "완료",
};

export function StageTimeline({ progress }: { progress?: IndexProgress }) {
  if (!progress) return null;
  const activeIndex =
    progress.status === "failed"
      ? 1
      : Math.max(0, STAGES.findIndex((stage) => stage === progress.status));
  const completed = progress.status === "done";

  return (
    <div
      className="mt-1.5"
      aria-label={`색인 단계: ${
        progress.status === "failed" ? "확인 필요" : STAGE_LABELS[STAGES[activeIndex]]
      }`}
    >
      <div className="grid grid-cols-3 gap-1">
        {STAGES.map((stage, index) => {
          const complete = completed || index < activeIndex;
          const active = !completed && progress.status !== "failed" && index === activeIndex;
          const failed = progress.status === "failed" && index === activeIndex;
          return (
            <span
              key={stage}
              title={failed ? "확인 필요" : STAGE_LABELS[stage]}
              className={cn(
                "h-1 rounded-full transition-all duration-300",
                complete && "bg-primary",
                active && "bg-primary/60 motion-safe:animate-pulse",
                !complete && !active && "bg-secondary",
                failed && "bg-amber-500",
              )}
            />
          );
        })}
      </div>
      <div className="mt-1 grid grid-cols-3 gap-1 text-[9px] font-medium leading-none text-muted-foreground/70">
        {STAGES.map((stage, index) => (
          <span
            key={stage}
            className={cn(
              "truncate",
              progress.status !== "failed" && index === activeIndex && "text-foreground/80",
              completed && index === activeIndex && "text-emerald-600 dark:text-emerald-400",
              progress.status === "failed" && index === activeIndex && "text-amber-600 dark:text-amber-500",
            )}
          >
            {progress.status === "failed" && index === activeIndex ? "확인" : STAGE_LABELS[stage]}
          </span>
        ))}
      </div>
    </div>
  );
}
