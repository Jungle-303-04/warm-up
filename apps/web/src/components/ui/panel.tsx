import type { ReactNode } from "react";

import { cn } from "../../lib/cn";

// 3패널 공통 셸(카드 톤). aside/section 시맨틱은 as로 선택.
export function Panel({
  as = "section",
  className,
  children,
}: {
  as?: "section" | "aside";
  className?: string;
  children: ReactNode;
}) {
  const Tag = as;
  return (
    <Tag
      className={cn(
        "flex flex-col overflow-hidden rounded-[16px] border border-border bg-card shadow-elev-1",
        className,
      )}
    >
      {children}
    </Tag>
  );
}
