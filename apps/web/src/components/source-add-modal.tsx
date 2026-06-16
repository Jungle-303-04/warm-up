"use client";

import { useEffect, useState, type ReactNode } from "react";

import { createSource } from "../lib/api";
import { cn } from "../lib/cn";
import { useWorkspace } from "../lib/store";
import type { Source, SourceCreate } from "../lib/types";
import { Icon } from "./icon";
import { Modal } from "./ui/modal";

type Tab = "url" | "repo";

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: "url", label: "URL", icon: "link" },
  { id: "repo", label: "GitHub 레포", icon: "github" },
];

// URL · 레포 추가 모달.
export function SourceAddModal({
  open,
  onClose,
  notebookId,
  initialTab = "url",
}: {
  open: boolean;
  onClose: () => void;
  notebookId: string;
  initialTab?: Tab;
}) {
  const [tab, setTab] = useState<Tab>(initialTab);
  const addSource = useWorkspace((s) => s.addSource);

  useEffect(() => {
    if (open) setTab(initialTab);
  }, [open, initialTab]);

  const submitSource = async (body: SourceCreate): Promise<Source> => {
    const source = await createSource(notebookId, body);
    addSource(source);
    return source;
  };

  return (
    <Modal open={open} onClose={onClose} title="URL · 레포 추가">
      <p className="mb-3 text-[12.5px] leading-relaxed text-muted-foreground">
        파일(PDF · Markdown · 텍스트)은 패널에 끌어다 놓거나 “소스 추가”로 선택하세요. 여기서는
        링크와 GitHub 레포를 등록합니다.
      </p>
      <div
        role="tablist"
        aria-label="소스 추가 방식"
        className="mb-4 flex gap-1 rounded-full bg-secondary p-1"
      >
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              "interactive flex flex-1 items-center justify-center gap-1.5 rounded-full px-2 py-1.5 text-[12px]",
              tab === t.id
                ? "bg-card font-semibold text-foreground shadow-elev-1"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            <Icon name={t.icon} size={15} />
            <span>{t.label}</span>
          </button>
        ))}
      </div>

      {tab === "url" ? (
        <UrlTab onSubmit={submitSource} onDone={onClose} />
      ) : (
        <RepoTab onSubmit={submitSource} onClose={onClose} />
      )}
    </Modal>
  );
}

function useSubmit(onSubmit: (body: SourceCreate) => Promise<Source>, onDone?: () => void) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (build: () => Promise<SourceCreate> | SourceCreate) => {
    setBusy(true);
    setError(null);
    try {
      const body = await build();
      await onSubmit(body);
      onDone?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "추가 실패");
    } finally {
      setBusy(false);
    }
  };

  return { busy, error, run };
}

function inferRepoTitle(url: string) {
  const m = url.match(/github\.com\/(?:[^/]+\/)?([^/]+\/.+?)(?:\.git)?\/?$/);
  return m ? m[1] : url;
}

// URL 입력: kind="url".
function UrlTab({ onSubmit, onDone }: { onSubmit: (body: SourceCreate) => Promise<Source>; onDone?: () => void }) {
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const { busy, error, run } = useSubmit(onSubmit, onDone);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        run(() => ({ kind: "url", title: title.trim() || url.trim(), url: url.trim() }));
      }}
      className="space-y-3"
    >
      <Field label="URL">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/docs"
          className={inputCls}
        />
      </Field>
      <Field label="제목 (선택)">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="비우면 URL을 제목으로 사용"
          className={inputCls}
        />
      </Field>
      {error ? <ErrorText>{error}</ErrorText> : null}
      <SubmitButton disabled={!url.trim() || busy}>{busy ? "추가 중…" : "URL 추가"}</SubmitButton>
    </form>
  );
}

// GitHub 레포 등록: repository_url + branch, kind="repo".
// 생성은 즉시 201 반환하고 인덱싱은 백그라운드에서 진행된다.
// 진행바는 소스 패널(SourceRow)이 SSE로 구독해 표시하므로 여기선 생성 후 닫기만 한다.
function RepoTab({
  onSubmit,
  onClose,
}: {
  onSubmit: (body: SourceCreate) => Promise<Source>;
  onClose: () => void;
}) {
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const { busy, error, run } = useSubmit(onSubmit, onClose);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const normalizedUrl = repoUrl.trim();
        if (!normalizedUrl) return;
        run(() => ({
          kind: "repo",
          title: inferRepoTitle(normalizedUrl),
          repository_url: normalizedUrl,
          branch: branch.trim() || "main",
        }));
      }}
      className="space-y-3"
    >
      <Field label="레포 URL">
        <input
          type="url"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          placeholder="https://github.com/org/repo"
          className={inputCls}
        />
      </Field>
      <Field label="브랜치">
        <input
          value={branch}
          onChange={(e) => setBranch(e.target.value)}
          placeholder="main"
          className={inputCls}
        />
      </Field>
      <p className="text-[12px] text-muted-foreground">
        등록하면 해당 브랜치를 백그라운드로 인덱싱합니다. 진행 상황은 소스 목록에서 실시간으로
        확인할 수 있어요.
      </p>
      {error ? <ErrorText>{error}</ErrorText> : null}
      <SubmitButton disabled={!repoUrl.trim() || busy}>
        {busy ? "레포 등록 중…" : "레포 등록"}
      </SubmitButton>
    </form>
  );
}

const inputCls =
  "interactive w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-[13px] outline-none placeholder:text-muted-foreground focus:border-primary/60 focus:ring-2 focus:ring-primary/15";

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block space-y-1.5">
      <span className="text-[13px] font-medium">{label}</span>
      {children}
    </label>
  );
}

function ErrorText({ children }: { children: React.ReactNode }) {
  return <p className="text-[12px] text-destructive">{children}</p>;
}

function SubmitButton({
  disabled,
  children,
}: {
  disabled: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      type="submit"
      disabled={disabled}
      className="interactive w-full rounded-full bg-primary py-2.5 text-[13px] font-medium text-primary-foreground hover:opacity-90 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-40 disabled:active:scale-100"
    >
      {children}
    </button>
  );
}
