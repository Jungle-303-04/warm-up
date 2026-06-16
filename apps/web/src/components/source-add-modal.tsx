"use client";

import { useState } from "react";

import { createSource } from "../lib/api";
import { cn } from "../lib/cn";
import { extractPdfText } from "../lib/pdf";
import { useWorkspace } from "../lib/store";
import type { SourceCreate } from "../lib/types";
import { Icon } from "./icon";
import { Modal } from "./ui/modal";

type Tab = "md" | "text" | "pdf" | "url" | "repo";

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: "md", label: "Markdown", icon: "description" },
  { id: "text", label: "텍스트", icon: "text_snippet" },
  { id: "pdf", label: "PDF", icon: "picture_as_pdf" },
  { id: "url", label: "URL", icon: "link" },
  { id: "repo", label: "GitHub", icon: "github" },
];

// 소스 추가 모달: ①Markdown ②텍스트 ③PDF(클라 추출) ④URL ⑤GitHub 레포.
export function SourceAddModal({
  open,
  onClose,
  notebookId,
}: {
  open: boolean;
  onClose: () => void;
  notebookId: string;
}) {
  const [tab, setTab] = useState<Tab>("md");
  const addSource = useWorkspace((s) => s.addSource);

  // 모든 탭이 공유하는 제출 핸들러: 생성 → 스토어 반영 → 닫기.
  const submit = async (body: SourceCreate) => {
    const source = await createSource(notebookId, body);
    addSource(source);
    onClose();
  };

  return (
    <Modal open={open} onClose={onClose} title="소스 추가">
      <div
        role="tablist"
        aria-label="소스 추가 방식"
        className="mb-4 flex gap-1 rounded-lg bg-secondary p-1"
      >
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              "flex flex-1 items-center justify-center gap-1.5 rounded-md px-2 py-1.5 text-[12px] transition-colors",
              tab === t.id
                ? "bg-card font-medium text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            <Icon name={t.icon} size={15} />
            <span className="hidden sm:inline">{t.label}</span>
          </button>
        ))}
      </div>

      {tab === "md" ? (
        <PasteTab kind="md" onSubmit={submit} />
      ) : tab === "text" ? (
        <PasteTab kind="text" onSubmit={submit} />
      ) : tab === "pdf" ? (
        <PdfTab onSubmit={submit} />
      ) : tab === "url" ? (
        <UrlTab onSubmit={submit} />
      ) : (
        <RepoTab onSubmit={submit} />
      )}
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

// Markdown · 텍스트 붙여넣기.
function PasteTab({
  kind,
  onSubmit,
}: {
  kind: "md" | "text";
  onSubmit: (body: SourceCreate) => Promise<void>;
}) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const { busy, error, run } = useSubmit(onSubmit);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        run(() => ({ kind, title: title.trim(), content }));
      }}
      className="space-y-3"
    >
      <Field label="제목">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder={kind === "md" ? "예: 아키텍처 노트" : "예: 회의록"}
          className={inputCls}
        />
      </Field>
      <Field label={kind === "md" ? "Markdown 내용" : "텍스트 내용"}>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={8}
          placeholder="내용을 붙여넣으세요"
          className={cn(inputCls, "resize-y font-mono")}
        />
      </Field>
      {error ? <ErrorText>{error}</ErrorText> : null}
      <SubmitButton disabled={!title.trim() || !content.trim() || busy}>
        {busy ? "추가 중…" : "소스 추가"}
      </SubmitButton>
    </form>
  );
}

// PDF 업로드: 클라이언트에서 pdfjs로 텍스트 추출 후 kind="pdf"로 POST.
function PdfTab({ onSubmit }: { onSubmit: (body: SourceCreate) => Promise<void> }) {
  const [file, setFile] = useState<File | null>(null);
  const { busy, error, run } = useSubmit(onSubmit);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (!file) return;
        run(async () => {
          const content = await extractPdfText(file);
          return { kind: "pdf", title: file.name, content };
        });
      }}
      className="space-y-3"
    >
      <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border py-8 text-center transition-colors hover:bg-secondary">
        <Icon name="picture_as_pdf" size={24} className="text-muted-foreground" />
        <span className="text-[13px]">{file?.name ?? "PDF 파일을 선택하세요"}</span>
        <span className="text-[12px] text-muted-foreground">
          텍스트를 브라우저에서 추출해 인덱싱합니다
        </span>
        <input
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
      </label>
      {error ? <ErrorText>{error}</ErrorText> : null}
      <SubmitButton disabled={!file || busy}>
        {busy ? "추출·추가 중…" : "PDF 추가"}
      </SubmitButton>
    </form>
  );
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
  "w-full rounded-lg border border-border bg-background px-3 py-2 text-[13px] outline-none placeholder:text-muted-foreground focus:border-ring";

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
      className="w-full rounded-full bg-primary py-2 text-[13px] font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
    >
      {children}
    </button>
  );
}
