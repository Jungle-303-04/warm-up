"use client";

import { useState } from "react";

import { createSource } from "../lib/api";
import { cn } from "../lib/cn";
import { useWorkspace } from "../lib/store";
import type { SourceCreate } from "../lib/types";
import { Icon } from "./icon";
import { Modal } from "./ui/modal";

// 파일류(MD/텍스트/PDF)는 드롭존·파일선택으로 옮겼고, 모달은 URL·레포 전용으로 축소.
type Tab = "url" | "repo";

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: "url", label: "URL", icon: "link" },
  { id: "repo", label: "GitHub 레포", icon: "github" },
];

// URL·레포 추가 전용 모달.
export function SourceAddModal({
  open,
  onClose,
  notebookId,
}: {
  open: boolean;
  onClose: () => void;
  notebookId: string;
}) {
  const [tab, setTab] = useState<Tab>("url");
  const addSource = useWorkspace((s) => s.addSource);

  // 두 탭이 공유하는 제출 핸들러: 생성 → 스토어 반영 → 닫기.
  const submit = async (body: SourceCreate) => {
    const source = await createSource(notebookId, body);
    addSource(source);
    onClose();
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

      {tab === "url" ? <UrlTab onSubmit={submit} /> : <RepoTab onSubmit={submit} />}
    </Modal>
  );
}

// 제출 상태(busy/error)를 공통 처리하는 래퍼.
function useSubmit(onSubmit: (body: SourceCreate) => Promise<void>) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const run = async (build: () => Promise<SourceCreate> | SourceCreate) => {
    setBusy(true);
    setError(null);
    try {
      const body = await build();
      await onSubmit(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "추가 실패");
    } finally {
      setBusy(false);
    }
  };
  return { busy, error, run };
}

// URL 입력: kind="url".
function UrlTab({ onSubmit }: { onSubmit: (body: SourceCreate) => Promise<void> }) {
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const { busy, error, run } = useSubmit(onSubmit);

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
      <SubmitButton disabled={!url.trim() || busy}>
        {busy ? "추가 중…" : "URL 추가"}
      </SubmitButton>
    </form>
  );
}

// GitHub 레포 등록: repository_url + branch, kind="repo".
function RepoTab({ onSubmit }: { onSubmit: (body: SourceCreate) => Promise<void> }) {
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const { busy, error, run } = useSubmit(onSubmit);

  // 제목은 owner/repo 형태로 추론.
  const inferTitle = (url: string) => {
    const m = url.match(/github\.com\/([^/]+\/[^/]+?)(?:\.git)?\/?$/);
    return m ? m[1] : url;
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        run(() => ({
          kind: "repo",
          title: inferTitle(repoUrl.trim()),
          repository_url: repoUrl.trim(),
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
        등록하면 해당 브랜치를 인덱싱합니다. 가시성은 GitHub 접근 권한을 따릅니다.
      </p>
      {error ? <ErrorText>{error}</ErrorText> : null}
      <SubmitButton disabled={!repoUrl.trim() || busy}>
        {busy ? "등록 중…" : "레포 등록"}
      </SubmitButton>
    </form>
  );
}

const inputCls =
  "interactive w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-[13px] outline-none placeholder:text-muted-foreground focus:border-primary/60 focus:ring-2 focus:ring-primary/15";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
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
