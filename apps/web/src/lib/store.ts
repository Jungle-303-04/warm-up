"use client";

import { create } from "zustand";

import { BOARD_TASKS, SOURCES } from "./fixtures";
import type { BoardTask, CenterTab } from "./types";

// 워크스페이스 전역 상태. 세 패널이 같은 "범위(선택 소스)"와 포커스를 공유한다.
interface WorkspaceStore {
  selected: Record<string, boolean>;
  focusedSourceId: string | null;
  centerTab: CenterTab;
  boardTasks: BoardTask[];
  activeThreadId: string | null;

  toggleSource: (id: string) => void;
  setAllSources: (on: boolean) => void;
  openSource: (id: string) => void; // 뷰어에 열기 + 뷰어 탭으로 이동
  setCenterTab: (tab: CenterTab) => void;
  addBoardTask: (task: Omit<BoardTask, "id">) => void; // 승인된 제안 → 보드 태스크
  openThread: (id: string) => void; // 스레드 열기 + 대화 탭으로 이동
  newThread: () => void; // 새 대화 시작
}

export const useWorkspace = create<WorkspaceStore>((set) => ({
  selected: Object.fromEntries(SOURCES.map((s) => [s.id, true])),
  focusedSourceId: null,
  centerTab: "대화",
  boardTasks: BOARD_TASKS,
  activeThreadId: null,

  toggleSource: (id) =>
    set((state) => ({ selected: { ...state.selected, [id]: !state.selected[id] } })),
  setAllSources: (on) =>
    set({ selected: Object.fromEntries(SOURCES.map((s) => [s.id, on])) }),
  openSource: (id) => set({ focusedSourceId: id, centerTab: "뷰어" }),
  setCenterTab: (tab) => set({ centerTab: tab }),
  addBoardTask: (task) =>
    set((state) => ({
      boardTasks: [{ ...task, id: `t-${Date.now()}` }, ...state.boardTasks],
    })),
  openThread: (id) => set({ activeThreadId: id, centerTab: "대화" }),
  newThread: () => set({ activeThreadId: null, centerTab: "대화" }),
}));

// 파생 셀렉터: 범위에 포함된 소스 개수.
export const selectScopeCount = (s: WorkspaceStore) =>
  Object.values(s.selected).filter(Boolean).length;
