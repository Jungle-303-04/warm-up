"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { SourceAddModal } from "../components/source-add-modal";
import { createSource } from "./api";
import { fileToSourceCreate } from "./file-source";
import { useWorkspace } from "./store";

// 소스 추가 흐름(파일선택·URL·레포)을 한 곳에서 소유한다.
// 좌측 소스 패널과 가운데 온보딩 히어로가 동일한 흐름을 호출할 수 있도록
// context로 노출한다(기능 계약 유지: createSource → addSource).
type AddTab = "url" | "repo";

interface SourceActions {
  openFilePicker: () => void; // 숨긴 file input 트리거
  openUrl: () => void; // URL 모달
  openRepo: () => void; // GitHub 레포 모달
  busy: boolean; // 파일 처리 중
  error: string | null;
  // 드래그앤드롭에서 파일 일괄 처리(소스 패널이 직접 호출).
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
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modal, setModal] = useState<{ open: boolean; tab: AddTab }>({ open: false, tab: "url" });

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

  const onPick = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) await processFiles(e.target.files);
      e.target.value = ""; // 같은 파일 재선택 허용
    },
    [processFiles],
  );

  const value = useMemo<SourceActions>(
    () => ({
      openFilePicker: () => fileInputRef.current?.click(),
      openUrl: () => setModal({ open: true, tab: "url" }),
      openRepo: () => setModal({ open: true, tab: "repo" }),
      busy,
      error,
      processFiles,
    }),
    [busy, error, processFiles],
  );

  return (
    <Ctx.Provider value={value}>
      {/* 시각적으로 숨긴 파일 input(어디서든 openFilePicker로 트리거) */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.md,.markdown,.txt,text/plain,text/markdown,application/pdf"
        className="hidden"
        onChange={onPick}
      />
      {children}
      {/* URL·레포 추가 모달은 흐름의 단일 소유자인 Provider가 렌더한다. */}
      <SourceAddModal
        open={modal.open}
        initialTab={modal.tab}
        notebookId={notebookId}
        onClose={() => setModal((m) => ({ ...m, open: false }))}
      />
    </Ctx.Provider>
  );
}
