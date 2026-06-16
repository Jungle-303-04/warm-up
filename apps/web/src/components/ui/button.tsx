"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "../../lib/cn";
import { Icon } from "../icon";

// 공용 알약 버튼 프리미티브. 전 영역의 버튼 크기/톤을 강제로 통일한다.
// - variant: primary(채움) | outline(테두리) | ghost(투명) | danger(파괴적)
// - size: sm(기본, h-7) | xs(더 작게, h-6)
// 아이콘 동반 시 gap이 적용되며, 로딩/아이콘은 props로 선언적으로 붙인다.
export type ButtonVariant = "primary" | "outline" | "ghost" | "danger";
export type ButtonSize = "sm" | "xs";

// variant별 색/테두리/호버. disabled 상태 포함.
const VARIANT: Record<ButtonVariant, string> = {
  primary:
    "bg-primary text-primary-foreground hover:opacity-90 active:scale-[0.98] disabled:opacity-40 disabled:active:scale-100",
  outline:
    "border border-border text-muted-foreground hover:bg-secondary hover:text-foreground active:scale-[0.98] disabled:opacity-40 disabled:hover:bg-transparent disabled:active:scale-100",
  ghost:
    "text-muted-foreground hover:bg-secondary hover:text-foreground active:scale-[0.98] disabled:opacity-40 disabled:hover:bg-transparent disabled:active:scale-100",
  danger:
    "border border-destructive/40 text-destructive hover:bg-destructive/10 active:scale-[0.98] disabled:opacity-40 disabled:hover:bg-transparent disabled:active:scale-100",
};

// size별 높이/패딩/폰트. 알약 형태(rounded-full)로 통일.
const SIZE: Record<ButtonSize, string> = {
  sm: "h-7 px-3 text-[12px] gap-1.5",
  xs: "h-6 px-2.5 text-[11px] gap-1",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  // 왼쪽 아이콘 이름(Icon name). loading=true면 회전 스피너로 대체된다.
  icon?: string;
  // 진행 중 표시(아이콘을 스피너로, disabled 처리). label은 그대로 둔다.
  loading?: boolean;
  // 아이콘만 두는 버튼은 false로(원형 hit area). 기본은 알약.
  pill?: boolean;
  children?: ReactNode;
}

export function Button({
  variant = "primary",
  size = "sm",
  icon,
  loading = false,
  pill = true,
  disabled,
  className,
  children,
  type = "button",
  ...rest
}: ButtonProps) {
  // 아이콘 사이즈는 size에 맞춰 작게.
  const iconSize = size === "xs" ? 12 : 13;
  return (
    <button
      type={type}
      disabled={disabled || loading}
      className={cn(
        "transition-all duration-200 ease-in-out inline-flex shrink-0 items-center justify-center font-medium",
        pill ? "rounded-full" : "rounded-lg",
        "disabled:cursor-not-allowed",
        SIZE[size],
        VARIANT[variant],
        className,
      )}
      {...rest}
    >
      {loading ? (
        <Icon name="progress_activity" size={iconSize} className="animate-spin" />
      ) : icon ? (
        <Icon name={icon} size={iconSize} />
      ) : null}
      {children}
    </button>
  );
}
