"use client";

import { useState } from "react";

import { cn } from "../lib/cn";
import { Icon } from "./icon";
import { Modal } from "./ui/modal";

type Tab = "repo" | "upload";

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: "repo", label: "GitHub 레포", icon: "github" },
  { id: "upload", label: "파일 업로드", icon: "description" },
];

// 소스 추가 모달(D4): ①GitHub 레포 URL 연결 ②파일 업로드(md/txt/pdf·10MB). 목업이라 제출=닫기.
// TODO(backend): repo=레포 연결 인덱싱, upload=파일 업로드 인덱싱 API와 연결.
export function SourceAddModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [tab, setTab] = useState<Tab>("repo");

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
              "flex flex-1 items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-[13px] transition-colors",
              tab === t.id
                ? "bg-card font-medium text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            <Icon name={t.icon} size={16} />
            {t.label}
          </button>
        ))}
      </div>

      {tab === "repo" ? <RepoTab onSubmit={onClose} /> : <UploadTab onSubmit={onClose} />}
    </Modal>
  );
}

function RepoTab({ onSubmit }: { onSubmit: () => void }) {
  const [url, setUrl] = useState("");

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
      className="space-y-3"
    >
      <label className="block space-y-1.5">
        <span className="text-[13px] font-medium">레포 URL</span>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://github.com/org/repo"
          className="w-full rounded-lg border border-border bg-background px-3 py-2 text-[13px] outline-none placeholder:text-muted-foreground focus:border-ring"
        />
      </label>
      <p className="text-[12px] text-muted-foreground">
        연결하면 저장소의 모든 브랜치를 인덱싱합니다. 가시성은 GitHub 접근 권한을 따릅니다.
      </p>
      <SubmitButton disabled={!url.trim()}>레포 연결</SubmitButton>
    </form>
  );
}

function UploadTab({ onSubmit }: { onSubmit: () => void }) {
  const [fileName, setFileName] = useState<string | null>(null);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
      className="space-y-3"
    >
      <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border py-8 text-center transition-colors hover:bg-secondary">
        <Icon name="add_circle" size={24} className="text-muted-foreground" />
        <span className="text-[13px]">{fileName ?? "파일을 선택하세요"}</span>
        <span className="text-[12px] text-muted-foreground">md · txt · pdf · 최대 10MB</span>
        <input
          type="file"
          accept=".md,.txt,.pdf"
          className="hidden"
          onChange={(e) => setFileName(e.target.files?.[0]?.name ?? null)}
        />
      </label>
      <SubmitButton disabled={!fileName}>업로드</SubmitButton>
    </form>
  );
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
