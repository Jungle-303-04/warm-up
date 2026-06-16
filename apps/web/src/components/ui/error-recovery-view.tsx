"use client";

import { Icon } from "../icon";

interface ErrorRecoveryViewProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
}

export function ErrorRecoveryView({
  title = "오류가 발생했습니다",
  message,
  onRetry,
  retryLabel = "다시 시도",
}: ErrorRecoveryViewProps) {
  return (
    <div className="flex flex-col items-center justify-center p-6 text-center border border-destructive/20 bg-destructive/5 rounded-2xl max-w-md mx-auto my-4 transition-all hover:border-destructive/30">
      <span className="grid h-12 w-12 place-items-center rounded-full bg-destructive/10 text-destructive mb-4">
        <Icon name="error_outline" size={24} />
      </span>
      <h3 className="text-[15px] font-semibold text-foreground mb-1.5">{title}</h3>
      <p className="text-[13px] text-muted-foreground leading-relaxed mb-4">{message}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="transition-all duration-200 ease-in-out inline-flex items-center gap-1.5 rounded-full bg-destructive/10 hover:bg-destructive/15 text-destructive px-4 py-1.5 text-[12px] font-semibold transition-all active:scale-[0.98]"
        >
          <Icon name="refresh" size={15} />
          {retryLabel}
        </button>
      ) : null}
    </div>
  );
}
