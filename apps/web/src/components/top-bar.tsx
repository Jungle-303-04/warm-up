"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { updateNotebook } from "../lib/api";
import { AuthMenu } from "./auth-menu";
import { Icon } from "./icon";
import { ThemeToggle } from "./theme-toggle";
import { IconButton } from "./ui/icon-button";

export function TopBar({
  notebookId,
  notebookTitle,
}: {
  notebookId: string;
  notebookTitle: string;
}) {
  // 인라인 제목 편집: 클릭 → input, Enter/blur 시 PATCH updateNotebook.
  const [title, setTitle] = useState(notebookTitle);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(notebookTitle);
  const [saving, setSaving] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  // 외부 title prop이 바뀌면 동기화(초기 로드 이후 재진입 대비).
  useEffect(() => setTitle(notebookTitle), [notebookTitle]);

  useEffect(() => {
    if (editing) inputRef.current?.select();
  }, [editing]);

  const startEdit = () => {
    setDraft(title);
    setEditing(true);
  };

  const commit = async () => {
    const next = draft.trim();
    setEditing(false);
    if (!next || next === title) {
      setDraft(title);
      return;
    }
    // 낙관적 반영 후 PATCH. 실패 시 이전 값으로 롤백.
    const prev = title;
    setTitle(next);
    setSaving(true);
    try {
      await updateNotebook(notebookId, { title: next });
    } catch {
      setTitle(prev);
    } finally {
      setSaving(false);
    }
  };

  return (
    <header className="flex h-[60px] shrink-0 items-center justify-between border-b border-border/70 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="flex min-w-0 items-center gap-1">
        <Link
          href="/"
          className="interactive flex items-center gap-2 rounded-full px-2 py-1.5 hover:bg-secondary"
          title="대시보드로"
        >
          <span className="grid h-7 w-7 place-items-center rounded-lg bg-accent text-accent-foreground">
            <Icon name="hub" size={17} />
          </span>
          <span className="text-[15px] font-semibold tracking-tight">RepoLM</span>
        </Link>
        <Icon name="chevron_right" size={16} className="shrink-0 text-muted-foreground/50" />

        {/* 인라인 편집 가능한 노트북 제목 */}
        {editing ? (
          <input
            ref={inputRef}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onBlur={commit}
            onKeyDown={(e) => {
              if (e.key === "Enter") commit();
              else if (e.key === "Escape") {
                setDraft(title);
                setEditing(false);
              }
            }}
            aria-label="노트북 제목"
            className="min-w-0 max-w-[40ch] rounded-lg border border-primary/50 bg-card px-2 py-1 text-[14px] font-medium outline-none ring-2 ring-primary/15"
          />
        ) : (
          <button
            type="button"
            onClick={startEdit}
            title="제목 편집"
            className="interactive group flex min-w-0 items-center gap-1.5 rounded-lg px-2 py-1 hover:bg-secondary"
          >
            <span className="truncate text-[14px] font-medium">{title}</span>
            {saving ? (
              <Icon name="progress_activity" size={13} className="shrink-0 animate-spin text-muted-foreground" />
            ) : (
              <Icon
                name="edit"
                size={13}
                className="shrink-0 text-muted-foreground/0 transition-colors group-hover:text-muted-foreground/70"
              />
            )}
          </button>
        )}
      </div>

      <div className="flex items-center gap-1">
        <button
          type="button"
          disabled
          title="공유 · 준비 중"
          className="interactive mr-1 inline-flex items-center gap-1.5 rounded-full border border-border px-3.5 py-1.5 text-[13px] font-medium text-muted-foreground hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:bg-transparent"
        >
          <Icon name="share" size={16} /> 공유
        </button>
        <IconButton name="settings" label="설정" size={18} preparing />
        <ThemeToggle />
        <span className="mx-0.5 h-5 w-px bg-border" aria-hidden />
        <AuthMenu />
      </div>
    </header>
  );
}
