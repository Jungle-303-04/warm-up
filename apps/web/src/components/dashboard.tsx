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
      <header className="flex h-14 items-center justify-between px-6">
        <div className="flex items-center gap-2">
          <Icon name="hub" size={22} className="text-primary" />
          <span className="text-[15px] font-semibold">RepoLM</span>
        </div>
        <div className="flex items-center gap-1">
          <ThemeToggle />
          <AuthMenu />
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl px-6 py-8">
        <div className="flex items-end justify-between">
          <div>
            <h1 className="text-[24px] font-semibold">노트북</h1>
            <p className="mt-1 text-[13px] text-muted-foreground">
              저장소와 문서를 모아 근거 기반으로 질문하세요.
            </p>
          </div>
          <button
            type="button"
            onClick={handleCreate}
            disabled={creating}
            className="inline-flex items-center gap-1.5 rounded-full bg-primary px-4 py-2 text-[13px] font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            <Icon name="add" size={18} /> {creating ? "만드는 중…" : "새 노트북 만들기"}
          </button>
        </div>

        {loading ? (
          <div className="mt-16 grid place-items-center text-muted-foreground">
            <Icon name="progress_activity" size={24} className="animate-spin" />
          </div>
        ) : error ? (
          <p className="mt-16 text-center text-[13px] text-destructive">{error}</p>
        ) : notebooks.length === 0 ? (
          <EmptyState onCreate={handleCreate} />
        ) : (
          <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
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

function EmptyState({ onCreate }: { onCreate: () => void }) {
  return (
    <div className="mt-12 grid place-items-center rounded-2xl border border-dashed border-border py-20 text-center">
      <span className="grid h-14 w-14 place-items-center rounded-2xl bg-secondary text-muted-foreground">
        <Icon name="hub" size={26} />
      </span>
      <p className="mt-4 text-[15px] font-semibold">아직 노트북이 없습니다</p>
      <p className="mt-1 max-w-xs text-[13px] leading-relaxed text-muted-foreground">
        첫 노트북을 만들고 GitHub 저장소·문서·PDF를 소스로 추가해 보세요.
      </p>
      <button
        type="button"
        onClick={onCreate}
        className="mt-5 inline-flex items-center gap-1.5 rounded-full bg-primary px-4 py-2 text-[13px] font-medium text-primary-foreground transition-opacity hover:opacity-90"
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
  return (
    <div className="group relative flex flex-col rounded-2xl border border-border bg-card p-4 shadow-sm transition-colors hover:border-primary/40">
      <button
        type="button"
        onClick={onOpen}
        className="flex flex-1 flex-col items-start text-left"
      >
        <span className="grid h-10 w-10 place-items-center rounded-xl bg-primary/10 text-primary">
          <Icon name="hub" size={20} />
        </span>
        <h3 className="mt-3 line-clamp-2 text-[15px] font-semibold leading-snug">
          {notebook.title}
        </h3>
        {notebook.summary ? (
          <p className="mt-1 line-clamp-2 text-[12px] leading-relaxed text-muted-foreground">
            {notebook.summary}
          </p>
        ) : null}
        <span className="mt-3 text-[11px] text-muted-foreground">
          소스 {notebook.source_count}개
        </span>
      </button>

      <div className="absolute right-2 top-2">
        <button
          type="button"
          aria-label="노트북 메뉴"
          onClick={() => setMenuOpen((o) => !o)}
          className="grid h-8 w-8 place-items-center rounded-full text-muted-foreground opacity-0 transition-opacity hover:bg-secondary group-hover:opacity-100"
        >
          <Icon name="more_vert" size={18} />
        </button>
        {menuOpen ? (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
            <div className="absolute right-0 z-20 mt-1 w-32 overflow-hidden rounded-lg border border-border bg-card py-1 shadow-lg">
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
        "flex w-full items-center gap-2 px-3 py-1.5 text-left text-[13px] transition-colors hover:bg-secondary",
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
          className="w-full rounded-lg border border-border bg-background px-3 py-2 text-[13px] outline-none placeholder:text-muted-foreground focus:border-ring"
        />
        {error ? <p className="text-[12px] text-destructive">{error}</p> : null}
        <button
          type="submit"
          disabled={!title.trim() || busy}
          className="w-full rounded-full bg-primary py-2 text-[13px] font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {busy ? "저장 중…" : "저장"}
        </button>
      </form>
    </Modal>
  );
}
