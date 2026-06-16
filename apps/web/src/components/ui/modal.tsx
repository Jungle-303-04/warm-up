"use client";

import { useEffect, type ReactNode } from "react";

import { cn } from "../../lib/cn";
import { IconButton } from "./icon-button";

// 재사용 접근성 다이얼로그. position:fixed 대신 absolute inset-0 인플로우 오버레이로 동작하므로
// 부모는 relative(보통 화면을 덮는 앱 루트)여야 한다. Esc·오버레이 클릭으로 닫힌다.
export function Modal({
  open,
  onClose,
  title,
  children,
  className,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  className?: string;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="absolute inset-0 z-50 grid place-items-center bg-black/50 p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
        className={cn(
          "flex max-h-full w-full max-w-lg flex-col overflow-hidden rounded-3xl border border-border bg-card text-card-foreground shadow-elev-3",
          className,
        )}
      >
        <header className="flex items-center justify-between border-b border-border px-5 py-3.5">
          <h2 className="text-[15px] font-semibold">{title}</h2>
          <IconButton name="close" label="닫기" size={16} onClick={onClose} />
        </header>
        <div className="scroll-thin overflow-y-auto p-5">{children}</div>
      </div>
    </div>
  );
}
