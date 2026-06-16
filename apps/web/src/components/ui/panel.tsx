import type { CSSProperties, ReactNode } from "react";

import { cn } from "../../lib/cn";

// 3패널 공통 셸(카드 톤). aside/section 시맨틱은 as로 선택.
export function Panel({
  as = "section",
  className,
  style,
  children,
}: {
  as?: "section" | "aside";
  className?: string;
  // 동적 너비 등 불가피한 인라인 스타일 주입용.
  style?: CSSProperties;
  children: ReactNode;
}) {
  const Tag = as;
  return (
    <Tag
      className={cn(
        "flex flex-col overflow-hidden rounded-[24px] border border-border/80 bg-card shadow-sm",
        className,
      )}
      style={style}
    >
      {children}
    </Tag>
  );
}
