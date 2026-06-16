"use client";

import React, { useState } from "react";
import { Modal } from "./ui/modal";

interface CreateNotebookModalProps {
  open: boolean;
  onClose: () => void;
  onCreate: (title: string, summary: string) => Promise<void>;
}

export function CreateNotebookModal({
  open,
  onClose,
  onCreate,
}: CreateNotebookModalProps) {
  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setBusy(true);
    setError(null);
    try {
      await onCreate(title.trim(), summary.trim());
      setTitle("");
      setSummary("");
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "생성 실패");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="새 노트북 만들기">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <label htmlFor="notebook-title" className="text-[12px] font-semibold text-muted-foreground">
            노트북 제목
          </label>
          <input
            id="notebook-title"
            autoFocus
            required
            placeholder="예: 프로젝트 가이드 분석"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="transition-all duration-200 ease-in-out w-full rounded-2xl border border-border bg-background px-4 py-2.5 text-[13px] outline-none placeholder:text-muted-foreground focus:border-primary/60 focus:ring-2 focus:ring-primary/15"
          />
        </div>

        <div className="space-y-1.5">
          <label htmlFor="notebook-summary" className="text-[12px] font-semibold text-muted-foreground">
            노트북 설명 (선택 사항)
          </label>
          <textarea
            id="notebook-summary"
            placeholder="노트북에 대한 짧은 설명을 입력하세요."
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            rows={3}
            className="transition-all duration-200 ease-in-out w-full rounded-2xl border border-border bg-background px-4 py-2.5 text-[13px] outline-none placeholder:text-muted-foreground focus:border-primary/60 focus:ring-2 focus:ring-primary/15 resize-none"
          />
        </div>

        {error ? <p className="text-[12px] text-destructive">{error}</p> : null}

        <button
          type="submit"
          disabled={!title.trim() || busy}
          className="transition-all duration-200 ease-in-out w-full rounded-full bg-primary py-2.5 text-[13px] font-medium text-primary-foreground hover:opacity-90 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-40 disabled:active:scale-100"
        >
          {busy ? "만드는 중…" : "만들기"}
        </button>
      </form>
    </Modal>
  );
}
