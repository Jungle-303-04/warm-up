"use client";

import Link from "next/link";

import { AuthMenu } from "./auth-menu";
import { Icon } from "./icon";
import { ThemeToggle } from "./theme-toggle";

export function TopBar({ notebookTitle }: { notebookTitle: string }) {
  return (
    <header className="flex h-[60px] shrink-0 items-center justify-between px-4">
      <div className="flex min-w-0 items-center gap-1.5">
        <Link
          href="/"
          className="interactive flex items-center gap-2 rounded-full px-2.5 py-1.5 hover:bg-secondary"
          title="대시보드로"
        >
          <span className="grid h-7 w-7 place-items-center rounded-lg bg-accent text-accent-foreground">
            <Icon name="hub" size={17} />
          </span>
          <span className="text-[15px] font-semibold tracking-tight">RepoLM</span>
        </Link>
        <Icon name="chevron_right" size={16} className="shrink-0 text-muted-foreground/60" />
        <span className="truncate text-[14px] font-medium">{notebookTitle}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <button
          type="button"
          disabled
          title="공유 · 준비 중"
          className="interactive mr-0.5 inline-flex items-center gap-1.5 rounded-full border border-border px-3.5 py-1.5 text-[13px] font-medium text-muted-foreground hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:bg-transparent"
        >
          <Icon name="share" size={16} /> 공유
        </button>
        <ThemeToggle />
        <AuthMenu />
      </div>
    </header>
  );
}
