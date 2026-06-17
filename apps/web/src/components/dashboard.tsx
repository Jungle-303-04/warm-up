"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  createNotebook,
  deleteNotebook,
  listNotebooks,
  updateNotebook,
} from "../lib/api";
import { cn } from "../lib/cn";
import type { Notebook } from "../lib/types";
import { AuthMenu } from "./auth-menu";
import { Icon } from "./icon";
import { ThemeToggle } from "./theme-toggle";
import { Modal } from "./ui/modal";
import { ErrorRecoveryView } from "./ui/error-recovery-view";

// 대시보드(홈): 노트북 카드 그리드 + 생성/이름변경/삭제(CRUD).
export function Dashboard() {
  const router = useRouter();
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [renaming, setRenaming] = useState<Notebook | null>(null);

  const loadNotebooks = () => {
    setLoading(true);
    setError(null);
    listNotebooks()
      .then((res) => setNotebooks(res.notebooks))
      .catch((e) => setError(e instanceof Error ? e.message : "불러오기 실패"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadNotebooks();
  }, []);

  const handleCreate = async () => {
    if (creating) return;
    setCreating(true);
    try {
      const nb = await createNotebook({ title: "새 노트북" });
      router.push(`/notebooks/${nb.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "생성 실패");
      setCreating(false);
    }
  };

  const handleRename = async (id: string, title: string) => {
    const updated = await updateNotebook(id, { title });
    setNotebooks((prev) => prev.map((n) => (n.id === id ? updated : n)));
    setRenaming(null);
  };

  const handleDelete = async (id: string) => {
    await deleteNotebook(id);
    setNotebooks((prev) => prev.filter((n) => n.id !== id));
  };

  return (
    <div className="relative min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-10 flex h-[52px] items-center justify-between border-b border-border/50 bg-background/90 px-5 backdrop-blur-lg">
        <div className="flex items-center gap-2">
          <span className="grid h-7 w-7 place-items-center rounded-full bg-primary/15 text-primary">
            <Icon name="hub" size={15} />
          </span>
          <span className="text-[14.5px] font-semibold tracking-tight">RepoLM</span>
        </div>
        <div className="flex items-center gap-1.5">
          <ThemeToggle />
          <AuthMenu />
        </div>
      </header>

      <main className="mx-auto w-full max-w-[960px] px-6 py-10">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-[24px] font-bold tracking-tight">노트북</h1>
            <p className="mt-1 text-[13px] text-muted-foreground">
              저장소와 문서를 모아 근거 기반으로 질문하세요.
            </p>
          </div>
          <button
            type="button"
            onClick={handleCreate}
            disabled={creating}
            className="transition-all duration-150 ease-out inline-flex items-center gap-1.5 rounded-full bg-primary px-4 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90 active:scale-[0.97] disabled:opacity-50"
          >
            <Icon
              name={creating ? "progress_activity" : "add"}
              size={17}
              className={creating ? "animate-spin" : ""}
            />
            {creating ? "생성 중…" : "새 노트북 만들기"}
          </button>
        </div>

        {loading ? (
          <div className="mt-20 grid place-items-center text-muted-foreground">
            <Icon name="progress_activity" size={26} className="animate-spin" />
          </div>
        ) : error ? (
          <div className="mt-16">
            <ErrorRecoveryView
              message={error}
              onRetry={loadNotebooks}
            />
          </div>
        ) : notebooks.length === 0 ? (
          <EmptyState onCreate={handleCreate} creating={creating} />
        ) : (
          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {notebooks.map((nb) => (
              <NotebookCard
                key={nb.id}
                notebook={nb}
                onOpen={() => router.push(`/notebooks/${nb.id}`)}
                onRename={() => setRenaming(nb)}
                onDelete={() => handleDelete(nb.id)}
              />
            ))}
          </div>
        )}
      </main>

      <RenameModal
        notebook={renaming}
        onClose={() => setRenaming(null)}
        onRename={handleRename}
      />
    </div>
  );
}

// ISO 날짜 → "2026. 6. 16." 형태. 파싱 실패 시 빈 문자열.
function formatDate(iso: string | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(d);
}

function EmptyState({
  onCreate,
  creating,
}: {
  onCreate: () => void;
  creating: boolean;
}) {
  return (
    <div className="mt-16 grid place-items-center rounded-2xl border border-dashed border-border/60 py-20 text-center">
      <span className="grid h-12 w-12 place-items-center rounded-full bg-primary/10 text-primary">
        <Icon name="auto_awesome" size={24} />
      </span>
      <p className="mt-4 text-[15px] font-semibold">아직 노트북이 없습니다</p>
      <p className="mt-1.5 max-w-sm text-[13px] leading-relaxed text-muted-foreground">
        첫 노트북을 만들고 GitHub 저장소·문서·PDF를 소스로 추가해 보세요.
      </p>
      <button
        type="button"
        onClick={onCreate}
        disabled={creating}
        className="transition-all duration-200 ease-in-out mt-5 inline-flex items-center gap-1.5 rounded-full bg-primary px-4 py-2 text-[12.5px] font-medium text-primary-foreground shadow-sm hover:opacity-90 hover:shadow active:scale-[0.98]"
      >
        <Icon
          name={creating ? "progress_activity" : "add"}
          size={17}
          className={creating ? "animate-spin" : ""}
        />
        {creating ? "생성 중…" : "새 노트북 만들기"}
      </button>
    </div>
  );
}

function NotebookCard({
  notebook,
  onOpen,
  onRename,
  onDelete,
}: {
  notebook: Notebook;
  onOpen: () => void;
  onRename: () => void;
  onDelete: () => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const dateLabel = formatDate(notebook.updated_at || notebook.created_at);
  return (
    <div className="group transition-all duration-200 ease-out relative flex min-h-[160px] overflow-hidden rounded-2xl border border-border/60 bg-card hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5">
      <button
        type="button"
        onClick={onOpen}
        className="flex flex-1 flex-col items-start p-5 text-left"
      >
        <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary/10 text-primary">
          <Icon name="book" size={15} />
        </span>
        <h3 className="mt-3 line-clamp-2 text-[14.5px] font-semibold leading-snug tracking-tight text-foreground group-hover:text-primary transition-colors duration-150">
          {notebook.title}
        </h3>
        <span className="mt-auto flex items-center gap-1.5 pt-3 text-[11px] font-medium text-muted-foreground/70">
          <span className="inline-flex items-center gap-1">
            <Icon name="folder_open" size={12} />
            소스 {notebook.source_count}개
          </span>
          {dateLabel ? (
            <>
              <span aria-hidden className="text-muted-foreground/35">
                ·
              </span>
              <span>{dateLabel}</span>
            </>
          ) : null}
        </span>
      </button>

      <div className="absolute right-3 top-3">
        <button
          type="button"
          aria-label="노트북 메뉴"
          onClick={() => setMenuOpen((o) => !o)}
          className={cn(
            "transition-all duration-200 ease-in-out grid h-7 w-7 place-items-center rounded-full text-muted-foreground hover:bg-secondary group-hover:opacity-100",
            menuOpen ? "opacity-100" : "opacity-0",
          )}
        >
          <Icon name="more_vert" size={17} />
        </button>
        {menuOpen ? (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
            <div className="absolute right-0 z-20 mt-1 w-36 overflow-hidden rounded-2xl border border-border bg-card py-1.5 shadow-md">
              <MenuItem
                icon="edit"
                label="이름 변경"
                onClick={() => {
                  setMenuOpen(false);
                  onRename();
                }}
              />
              <MenuItem
                icon="delete"
                label="삭제"
                destructive
                onClick={() => {
                  setMenuOpen(false);
                  onDelete();
                }}
              />
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}

function MenuItem({
  icon,
  label,
  destructive = false,
  onClick,
}: {
  icon: string;
  label: string;
  destructive?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "transition-all duration-200 ease-in-out flex w-full items-center gap-2.5 px-3.5 py-2 text-left text-[13px] hover:bg-secondary",
        destructive ? "text-destructive" : "text-foreground",
      )}
    >
      <Icon name={icon} size={15} />
      {label}
    </button>
  );
}

function RenameModal({
  notebook,
  onClose,
  onRename,
}: {
  notebook: Notebook | null;
  onClose: () => void;
  onRename: (id: string, title: string) => Promise<void>;
}) {
  const [title, setTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (notebook) setTitle(notebook.title);
  }, [notebook]);

  if (!notebook) return null;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await onRename(notebook.id, title.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "변경 실패");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal open={!!notebook} onClose={onClose} title="이름 변경">
      <form onSubmit={submit} className="space-y-3">
        <input
          autoFocus
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="transition-all duration-200 ease-in-out w-full rounded-2xl border border-border bg-background px-4 py-2.5 text-[13px] outline-none placeholder:text-muted-foreground focus:border-primary/60 focus:ring-2 focus:ring-primary/15"
        />
        {error ? <p className="text-[12px] text-destructive">{error}</p> : null}
        <button
          type="submit"
          disabled={!title.trim() || busy}
          className="transition-all duration-200 ease-in-out w-full rounded-full bg-primary py-2.5 text-[13px] font-medium text-primary-foreground hover:opacity-90 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-40 disabled:active:scale-100"
        >
          {busy ? "저장 중…" : "저장"}
        </button>
      </form>
    </Modal>
  );
}
