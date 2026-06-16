"use client";

import Link from "next/link";

import { AuthMenu } from "./auth-menu";
import { Icon } from "./icon";
import { ThemeToggle } from "./theme-toggle";

export function TopBar({ notebookTitle }: { notebookTitle: string }) {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between px-4">
      <div className="flex min-w-0 items-center gap-2">
        <Link
          href="/"
          className="flex items-center gap-2 rounded-md px-1 py-1 transition-colors hover:bg-secondary"
          title="대시보드로"
        >
          <Icon name="hub" size={22} className="text-primary" />
          <span className="text-[15px] font-semibold">RepoLM</span>
        </Link>
        <Icon name="chevron_right" size={18} className="shrink-0 text-muted-foreground" />
        <span className="truncate text-[14px] font-medium">{notebookTitle}</span>
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
        <ThemeToggle />
        <AuthMenu />
      </div>
    </header>
  );
}
