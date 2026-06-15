"use client";

import { AuthMenu } from "./auth-menu";
import { Icon } from "./icon";
import { ThemeToggle } from "./theme-toggle";

export function TopBar() {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between px-4">
      <div className="flex items-center gap-2">
        <Icon name="hub" size={22} className="text-primary" />
        <span className="text-[15px] font-semibold">RepoLM</span>
        <Icon name="chevron_right" size={18} className="text-muted-foreground" />
        <button
          type="button"
          disabled
          title="워크스페이스 전환 · 준비 중"
          className="inline-flex items-center gap-1 rounded-md px-1.5 py-1 text-[14px] text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-transparent"
        >
          team 워크스페이스
          <Icon name="unfold_more" size={16} />
        </button>
      </div>
      <div className="flex items-center gap-1">
        <button
          type="button"
          disabled
          title="공유 · 준비 중"
          className="mr-1 inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-[13px] text-muted-foreground transition-colors hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-transparent"
        >
          <Icon name="share" size={16} /> 공유
        </button>
        <button
          type="button"
          disabled
          title="알림 · 준비 중"
          aria-label="알림 · 준비 중"
          className="grid h-8 w-8 place-items-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-transparent"
        >
          <Icon name="notifications" size={18} />
        </button>
        <ThemeToggle />
        <AuthMenu />
      </div>
    </header>
  );
}
