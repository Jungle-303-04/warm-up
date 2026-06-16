"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { SourceAddModal } from "../components/source-add-modal";
import { createSource } from "./api";
import { fileToSourceCreate } from "./file-source";
import { useWorkspace } from "./store";

// 소스 추가 흐름(파일·URL·GitHub)을 한 곳에서 소유한다.
// 좌측 소스 패널과 가운데 온보딩 히어로가 동일한 흐름을 호출할 수 있도록
// context로 노출한다(기능 계약 유지: createSource → addSource).
// 파일/URL/GitHub 레포는 단일 "소스 추가" 모달로 통합됐다(진입점 일원화).

interface SourceActions {
  openAddSource: () => void; // 통합 소스 추가 모달(파일 드롭존 + URL/GitHub 입력)
  busy: boolean; // 파일 처리 중
  error: string | null;
  // 드래그앤드롭에서 파일 일괄 처리(소스 패널 전역 드롭존이 직접 호출).
  processFiles: (files: FileList | File[]) => Promise<void>;
}

const Ctx = createContext<SourceActions | null>(null);

export function useSourceActions(): SourceActions {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useSourceActions must be used within SourceActionsProvider");
  return ctx;
}

export function SourceActionsProvider({
  notebookId,
  children,
}: {
  notebookId: string;
  children: ReactNode;
}) {
  const addSource = useWorkspace((s) => s.addSource);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  // 파일 목록 순차 처리 → createSource → 스토어 반영. 실패는 모아서 표시.
  const processFiles = useCallback(
    async (files: FileList | File[]) => {
      const list = Array.from(files);
      if (list.length === 0) return;
      setBusy(true);
      setError(null);
      const failed: string[] = [];
      for (const file of list) {
        try {
          const body = await fileToSourceCreate(file);
          const source = await createSource(notebookId, body);
          addSource(source);
        } catch {
          failed.push(file.name);
        }
      }
      setBusy(false);
      if (failed.length > 0) setError(`추가 실패: ${failed.join(", ")}`);
    },
    [notebookId, addSource],
  );

  const value = useMemo<SourceActions>(
    () => ({
      openAddSource: () => setModalOpen(true),
      busy,
      error,
      processFiles,
    }),
    [busy, error, processFiles],
  );

  return (
    <Ctx.Provider value={value}>
      {children}
      {/* 통합 소스 추가 모달(파일 드롭존 + URL/GitHub)은 흐름의 단일 소유자인 Provider가 렌더한다. */}
      <SourceAddModal
        open={modalOpen}
        notebookId={notebookId}
        onClose={() => setModalOpen(false)}
        processFiles={processFiles}
        busy={busy}
      />
    </Ctx.Provider>
  );
}
