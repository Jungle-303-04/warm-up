"use client";

import { cn } from "../lib/cn";
import type { IndexProgress } from "../lib/types";
import { Icon } from "./icon";

export function IndexingStatusBadge({ progress }: { progress?: IndexProgress }) {
  if (!progress) {
    return (
      <span className="inline-flex items-center gap-1 rounded-md bg-secondary px-1.5 py-0.5 text-[10px] font-semibold text-muted-foreground">
        <Icon name="hourglass_empty" size={11} />
        대기
      </span>
    );
  }

  const active = progress.status === "queued" || progress.status === "running";
  const failed = progress.status === "failed";
  const label =
    progress.status === "done"
      ? `${progress.indexed_chunks} chunks`
      : failed
        ? "확인 필요"
        : `${progress.percent}%`;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-semibold",
        failed
          ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
          : active
            ? "bg-primary/10 text-primary"
            : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
      )}
      title={progress.content_hash ? `content hash: ${progress.content_hash.slice(0, 12)}` : undefined}
    >
      <Icon
        name={failed ? "refresh" : active ? "progress_activity" : "check_circle"}
        size={11}
        className={active ? "animate-spin" : ""}
      />
      {label}
    </span>
  );
}
