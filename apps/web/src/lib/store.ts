"use client";

import { create } from "zustand";

import type { CenterTab, Source } from "./types";

// 뷰어가 가리키는 대상: 소스 자체 또는 repo 소스 안의 특정 파일.
export interface ViewerTarget {
  sourceId: string;
  // path 가 있으면 repo 파일, 없으면 소스 본문.
  path?: string;
}

// 노트북 화면 전역 상태. 모든 소스는 자동으로 답변 범위에 포함된다(선택 개념 없음).
interface WorkspaceStore {
  notebookId: string | null;
  sources: Source[];
  viewer: ViewerTarget | null; // 중앙 뷰어가 여는 대상
  centerTab: CenterTab;

  initNotebook: (notebookId: string, sources: Source[]) => void;
  setSources: (sources: Source[]) => void;
  addSource: (source: Source) => void; // 소스 추가 후 목록 반영
  removeSource: (id: string) => void;

  openSource: (id: string) => void; // 소스 본문을 뷰어에 열기 + 뷰어 탭으로 이동
  openFile: (sourceId: string, path: string) => void; // repo 파일을 뷰어에 열기
  setCenterTab: (tab: CenterTab) => void;
}

export const useWorkspace = create<WorkspaceStore>((set) => ({
  notebookId: null,
  sources: [],
  viewer: null,
  centerTab: "대화",

  initNotebook: (notebookId, sources) =>
    set({ notebookId, sources, viewer: null, centerTab: "대화" }),
  setSources: (sources) => set({ sources }),
  addSource: (source) => set((state) => ({ sources: [source, ...state.sources] })),
  removeSource: (id) =>
    set((state) => ({
      sources: state.sources.filter((s) => s.id !== id),
      viewer: state.viewer?.sourceId === id ? null : state.viewer,
    })),

  openSource: (id) => set({ viewer: { sourceId: id }, centerTab: "뷰어" }),
  openFile: (sourceId, path) => set({ viewer: { sourceId, path }, centerTab: "뷰어" }),
  setCenterTab: (tab) => set({ centerTab: tab }),
}));

// 파생 셀렉터: 답변 범위 소스 개수(전체 소스 = 모두 자동 포함).
export const selectScopeCount = (s: WorkspaceStore) => s.sources.length;
