"use client";

import { create } from "zustand";

import type { CenterTab, Source } from "./types";

// 뷰어가 가리키는 대상: 소스 자체 또는 repo 소스 안의 특정 파일.
export interface ViewerTarget {
  sourceId: string;
  // path 가 있으면 repo 파일, 없으면 소스 본문.
  path?: string;
}

// 노트북 화면 전역 상태. 세 패널이 같은 "범위(선택 소스)"와 포커스를 공유한다.
interface WorkspaceStore {
  notebookId: string | null;
  sources: Source[];
  selected: Record<string, boolean>; // 답변 범위에 포함된 소스
  viewer: ViewerTarget | null; // 중앙 뷰어가 여는 대상
  centerTab: CenterTab;

  // 노트북 진입 시 소스 목록을 주입(모두 범위 포함으로 초기화).
  initNotebook: (notebookId: string, sources: Source[]) => void;
  setSources: (sources: Source[]) => void;
  addSource: (source: Source) => void; // 소스 추가 후 목록 반영
  removeSource: (id: string) => void;

  toggleSource: (id: string) => void;
  setAllSources: (on: boolean) => void;
  openSource: (id: string) => void; // 소스 본문을 뷰어에 열기 + 뷰어 탭으로 이동
  openFile: (sourceId: string, path: string) => void; // repo 파일을 뷰어에 열기
  setCenterTab: (tab: CenterTab) => void;
}

export const useWorkspace = create<WorkspaceStore>((set) => ({
  notebookId: null,
  sources: [],
  selected: {},
  viewer: null,
  centerTab: "대화",

  initNotebook: (notebookId, sources) =>
    set({
      notebookId,
      sources,
      selected: Object.fromEntries(sources.map((s) => [s.id, true])),
      viewer: null,
      centerTab: "대화",
    }),
  setSources: (sources) =>
    set((state) => ({
      sources,
      // 새 소스는 기본 범위 포함, 기존 선택은 유지.
      selected: Object.fromEntries(
        sources.map((s) => [s.id, state.selected[s.id] ?? true]),
      ),
    })),
  addSource: (source) =>
    set((state) => ({
      sources: [source, ...state.sources],
      selected: { ...state.selected, [source.id]: true },
    })),
  removeSource: (id) =>
    set((state) => {
      const { [id]: _drop, ...selected } = state.selected;
      return {
        sources: state.sources.filter((s) => s.id !== id),
        selected,
        viewer: state.viewer?.sourceId === id ? null : state.viewer,
      };
    }),

  toggleSource: (id) =>
    set((state) => ({ selected: { ...state.selected, [id]: !state.selected[id] } })),
  setAllSources: (on) =>
    set((state) => ({
      selected: Object.fromEntries(state.sources.map((s) => [s.id, on])),
    })),
  openSource: (id) => set({ viewer: { sourceId: id }, centerTab: "뷰어" }),
  openFile: (sourceId, path) => set({ viewer: { sourceId, path }, centerTab: "뷰어" }),
  setCenterTab: (tab) => set({ centerTab: tab }),
}));

// 파생 셀렉터: 범위에 포함된 소스 개수.
export const selectScopeCount = (s: WorkspaceStore) =>
  Object.values(s.selected).filter(Boolean).length;
