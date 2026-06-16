"use client";

import { useEffect, useState } from "react";

import { getNotebook } from "../lib/api";
import { useWorkspace } from "../lib/store";
import type { NotebookDetail } from "../lib/types";
import { CenterPanel } from "./center-panel";
import { Icon } from "./icon";
import { SourcesPanel } from "./sources-panel";
import { StudioPanel } from "./studio-panel";
import { TopBar } from "./top-bar";

// 노트북 워크스페이스. 진입 시 노트북 상세를 불러와 스토어를 초기화한다.
export function Workspace({ notebookId }: { notebookId: string }) {
  const [notebook, setNotebook] = useState<NotebookDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const initNotebook = useWorkspace((s) => s.initNotebook);

  useEffect(() => {
    let active = true;
    setLoading(true);
    getNotebook(notebookId)
      .then((detail) => {
        if (!active) return;
        setNotebook(detail);
        initNotebook(detail.id, detail.sources);
      })
      .catch((e) => active && setError(e instanceof Error ? e.message : "불러오기 실패"))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [notebookId, initNotebook]);

  if (loading) {
    return (
      <div className="grid h-screen place-items-center bg-background text-muted-foreground">
        <Icon name="progress_activity" size={28} className="animate-spin" />
      </div>
    );
  }

  if (error || !notebook) {
    return (
      <div className="grid h-screen place-items-center bg-background text-center text-muted-foreground">
        <div>
          <p className="text-[14px] font-semibold text-foreground">노트북을 열 수 없습니다</p>
          <p className="mt-1 text-[13px]">{error ?? "존재하지 않는 노트북입니다."}</p>
          <a href="/" className="mt-3 inline-block text-[13px] text-primary underline">
            대시보드로 돌아가기
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-background text-foreground">
      <TopBar notebookTitle={notebook.title} />
      <main className="flex flex-1 gap-3 overflow-hidden px-3 pb-3">
        <SourcesPanel notebookId={notebook.id} />
        <CenterPanel />
        <StudioPanel />
      </main>
    </div>
  );
}
