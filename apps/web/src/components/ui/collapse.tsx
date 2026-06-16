"use client";

import type { ReactNode } from "react";

import { cn } from "../../lib/cn";

// 재사용 여닫기 래퍼. grid-rows-[0fr→1fr] 트랜지션으로 콘텐츠 높이를 측정 없이
// 부드럽게 열고 닫는다(자식의 자연 높이를 그대로 사용). overflow-hidden으로
// 접힌 동안 콘텐츠가 새어나오지 않게 한다.
export function Collapse({
  open,
  children,
  className,
  durationMs = 200,
}: {
  open: boolean;
  children: ReactNode;
  className?: string;
  durationMs?: number;
}) {
  return (
    <div
      aria-hidden={!open}
      className={cn(
        "grid transition-[grid-template-rows,opacity] ease-out",
        open ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0",
        className,
      )}
      style={{ transitionDuration: `${durationMs}ms` }}
    >
      {/* min-h-0 + overflow-hidden 이 0fr 행을 실제로 0 높이로 만든다. */}
      <div className="min-h-0 overflow-hidden">{children}</div>
    </div>
  );
}
