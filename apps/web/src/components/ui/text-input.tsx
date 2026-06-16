"use client";

import type { InputHTMLAttributes } from "react";

import { cn } from "../../lib/cn";

// 공용 텍스트 입력 클래스 상수. 전 영역 입력 높이/폰트(h-8 px-3 text-[12px])를 통일한다.
// 컴포넌트 대신 클래스를 노출해 form/검색/모달 등 다양한 래퍼에서 자유롭게 조합한다.
export const TEXT_INPUT_CLS =
  "interactive h-8 w-full rounded-lg border border-border bg-background px-3 text-[12px] font-medium outline-none placeholder:font-normal placeholder:text-muted-foreground focus:border-primary/60 focus:ring-2 focus:ring-primary/15 disabled:cursor-not-allowed disabled:opacity-60";

// 클래스 상수를 그대로 입은 입력 컴포넌트(선택적 사용).
export function TextInput({ className, ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(TEXT_INPUT_CLS, className)} {...rest} />;
}
