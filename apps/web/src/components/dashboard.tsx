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

// 대시보드(홈): 노트북 카드 그리드 + 생성/이름변경/삭제(CRUD).
export function Dashboard() {
  const router = useRouter();
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [renaming, setRenaming] = useState<Notebook | null>(null);

  useEffect(() => {
    listNotebooks()
      .then((res) => setNotebooks(res.notebooks))
      .catch((e) => setError(e instanceof Error ? e.message : "불러오기 실패"))
      .finally(() => setLoading(false));
  }, []);

  // 생성 즉시 더미 제목으로 노트북을 만들고 바로 노트북 페이지로 진입한다.
  // (제목은 노트북 안에서 또는 카드 메뉴 "이름 변경"으로 수정)
  const handleCreate = async () => {
    if (creating) return;
    setCreating(true);
    try {
      const nb = await createNotebook({ title: "제목 없는 노트북" });
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
      <header className="sticky top-0 z-10 flex h-[60px] items-center justify-between border-b border-border/60 bg-background/80 px-6 backdrop-blur">
        <div className="flex items-center gap-2">
          <span className="grid h-7 w-7 place-items-center rounded-lg bg-accent text-accent-foreground">
            <Icon name="hub" size={17} />
          </span>
          <span className="text-[15px] font-semibold tracking-tight">RepoLM</span>
        </div>
        <div className="flex items-center gap-1.5">
          <ThemeToggle />
          <AuthMenu />
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl px-6 py-10">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-[26px] font-semibold tracking-tight">노트북</h1>
            <p className="mt-1.5 text-[13.5px] text-muted-foreground">
              저장소와 문서를 모아 근거 기반으로 질문하세요.
            </p>
          </div>
          <button
            type="button"
            onClick={handleCreate}
            disabled={creating}
            className="interactive inline-flex items-center gap-1.5 rounded-full bg-primary px-5 py-2.5 text-[13px] font-medium text-primary-foreground shadow-elev-1 hover:opacity-90 hover:shadow-elev-2 active:scale-[0.98] disabled:opacity-50"
          >
            <Icon name="add" size={18} /> {creating ? "만드는 중…" : "새 노트북 만들기"}
          </button>
        </div>

        {loading ? (
          <div className="mt-20 grid place-items-center text-muted-foreground">
            <Icon name="progress_activity" size={26} className="animate-spin" />
          </div>
        ) : error ? (
          <p className="mt-20 text-center text-[13px] text-destructive">{error}</p>
        ) : notebooks.length === 0 ? (
          <EmptyState onCreate={handleCreate} />
        ) : (
          <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
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

function EmptyState({ onCreate }: { onCreate: () => void }) {
  return (
    <div className="mt-14 grid place-items-center rounded-3xl border border-dashed border-border bg-card/40 py-24 text-center">
      <span className="grid h-16 w-16 place-items-center rounded-2xl bg-accent text-accent-foreground">
        <Icon name="hub" size={30} />
      </span>
      <p className="mt-5 text-[16px] font-semibold">아직 노트북이 없습니다</p>
      <p className="mt-1.5 max-w-sm text-[13.5px] leading-relaxed text-muted-foreground">
        첫 노트북을 만들고 GitHub 저장소·문서·PDF를 소스로 추가해 보세요.
      </p>
      <button
        type="button"
        onClick={onCreate}
        className="interactive mt-6 inline-flex items-center gap-1.5 rounded-full bg-primary px-5 py-2.5 text-[13px] font-medium text-primary-foreground shadow-elev-1 hover:opacity-90 hover:shadow-elev-2 active:scale-[0.98]"
      >
        <Icon name="add" size={18} /> 새 노트북 만들기
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
    <div className="group interactive relative flex min-h-[176px] flex-col rounded-2xl border border-border bg-card p-5 shadow-elev-1 hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-elev-2">
      <button
        type="button"
        onClick={onOpen}
        className="flex flex-1 flex-col items-start text-left"
      >
        <span className="grid h-11 w-11 place-items-center rounded-2xl bg-accent text-accent-foreground">
          <Icon name="hub" size={21} />
        </span>
        <h3 className="mt-3.5 line-clamp-2 text-[15px] font-semibold leading-snug tracking-tight">
          {notebook.title}
        </h3>
        {notebook.summary ? (
          <p className="mt-1.5 line-clamp-2 text-[12.5px] leading-relaxed text-muted-foreground">
            {notebook.summary}
          </p>
        ) : null}
        <span className="mt-auto flex items-center gap-1.5 pt-4 text-[11.5px] text-muted-foreground">
          <span>소스 {notebook.source_count}개</span>
          {dateLabel ? (
            <>
              <span aria-hidden className="text-muted-foreground/50">
                ·
              </span>
              <span>{dateLabel}</span>
            </>
          ) : null}
        </span>
      </button>

      <div className="absolute right-2.5 top-2.5">
        <button
          type="button"
          aria-label="노트북 메뉴"
          onClick={() => setMenuOpen((o) => !o)}
          className={cn(
            "interactive grid h-8 w-8 place-items-center rounded-full text-muted-foreground hover:bg-secondary group-hover:opacity-100",
            menuOpen ? "opacity-100" : "opacity-0",
          )}
        >
          <Icon name="more_vert" size={18} />
        </button>
        {menuOpen ? (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
            <div className="absolute right-0 z-20 mt-1 w-36 overflow-hidden rounded-xl border border-border bg-card py-1.5 shadow-elev-3">
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
        "interactive flex w-full items-center gap-2.5 px-3.5 py-2 text-left text-[13px] hover:bg-secondary",
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
          className="interactive w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-[13px] outline-none placeholder:text-muted-foreground focus:border-primary/60 focus:ring-2 focus:ring-primary/15"
        />
        {error ? <p className="text-[12px] text-destructive">{error}</p> : null}
        <button
          type="submit"
          disabled={!title.trim() || busy}
          className="interactive w-full rounded-full bg-primary py-2.5 text-[13px] font-medium text-primary-foreground hover:opacity-90 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-40 disabled:active:scale-100"
        >
          {busy ? "저장 중…" : "저장"}
        </button>
      </form>
    </Modal>
  );
}
