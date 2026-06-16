"use client";

import { create } from "zustand";

import type { CenterTab, IndexProgress, Source, StudioArtifact } from "./types";

// 뷰어가 가리키는 대상: 소스 자체 또는 repo 소스 안의 특정 파일.
export interface ViewerTarget {
  sourceId: string;
  // path 가 있으면 repo 파일, 없으면 소스 본문.
  path?: string;
}

export interface WorkspaceCacheSnapshot {
  selectedSourceIds?: string[];
  viewer?: ViewerTarget | null;
  centerTab?: CenterTab;
  artifacts?: StudioArtifact[];
  indexProgress?: Record<string, IndexProgress>;
}

// 노트북 화면 전역 상태. 모든 소스는 자동으로 답변 범위에 포함된다(선택 개념 없음).
interface WorkspaceStore {
  notebookId: string | null;
  sources: Source[];
  selectedSourceIds: Set<string>;
  viewer: ViewerTarget | null; // 중앙 뷰어가 여는 대상
  centerTab: CenterTab;
  artifacts: StudioArtifact[];
  // 소스별 RAG 인덱싱 진행(백엔드 SSE 스냅샷). key = sourceId.
  indexProgress: Record<string, IndexProgress>;

  initNotebook: (notebookId: string, sources: Source[]) => void;
  setSources: (sources: Source[]) => void;
  addSource: (source: Source) => void; // 소스 추가 후 목록 반영
  removeSource: (id: string) => void;
  toggleSourceSelected: (id: string) => void;
  setAllSourcesSelected: (selected: boolean) => void;
  hydrateCachedState: (snapshot: WorkspaceCacheSnapshot) => void;

  openSource: (id: string) => void; // 소스 본문을 뷰어에 열기 + 뷰어 탭으로 이동
  openFile: (sourceId: string, path: string) => void; // repo 파일을 뷰어에 열기
  setCenterTab: (tab: CenterTab) => void;
  setIndexProgress: (sourceId: string, progress: IndexProgress) => void;
  clearIndexProgress: (sourceId: string) => void;
  createArtifact: (artifact: Omit<StudioArtifact, "id" | "createdAt" | "sourceCount">) => void;
  addNote: (title?: string, detail?: string) => void;
}

const makeId = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;

const seedArtifacts = (sourceCount: number): StudioArtifact[] =>
  sourceCount === 0
    ? []
    : [
        {
          id: makeId(),
          kind: "artifact",
          title: "의존성 그래프",
          typeLabel: "그래프",
          detail: `소스 ${Math.min(sourceCount, 3)}개 · 방금 전`,
          icon: "dependency",
          tint: "teal",
          createdAt: Date.now() - 60_000,
          sourceCount,
        },
        {
          id: makeId(),
          kind: "artifact",
          title: "변경 요약",
          typeLabel: "Diff",
          detail: `소스 ${Math.min(sourceCount, 3)}개 · 방금 전`,
          icon: "diff",
          tint: "amber",
          createdAt: Date.now() - 30_000,
          sourceCount,
        },
      ];

export const useWorkspace = create<WorkspaceStore>((set) => ({
  notebookId: null,
  sources: [],
  selectedSourceIds: new Set(),
  viewer: null,
  centerTab: "대화",
  artifacts: [],
  indexProgress: {},

  initNotebook: (notebookId, sources) =>
    set({
      notebookId,
      sources,
      selectedSourceIds: new Set(sources.map((s) => s.id)),
      viewer: null,
      centerTab: "대화",
      indexProgress: {},
      artifacts: seedArtifacts(sources.length),
    }),
  setSources: (sources) =>
    set((state) => {
      const nextSourceIds = new Set(sources.map((source) => source.id));
      // 사라진 소스의 진행 상태는 정리한다.
      const indexProgress: Record<string, IndexProgress> = {};
      for (const [id, progress] of Object.entries(state.indexProgress)) {
        if (nextSourceIds.has(id)) indexProgress[id] = progress;
      }

      return {
        sources,
        selectedSourceIds: new Set(
          sources
            .map((s) => s.id)
            .filter((id) => state.selectedSourceIds.has(id) || state.selectedSourceIds.size === 0),
        ),
        indexProgress,
      };
    }),
  addSource: (source) =>
    set((state) => ({
      sources: [source, ...state.sources],
      selectedSourceIds: new Set([source.id, ...state.selectedSourceIds]),
    })),
  removeSource: (id) =>
    set((state) => {
      const selectedSourceIds = new Set(state.selectedSourceIds);
      selectedSourceIds.delete(id);
      const indexProgress = { ...state.indexProgress };
      delete indexProgress[id];
      return {
        sources: state.sources.filter((s) => s.id !== id),
        selectedSourceIds,
        viewer: state.viewer?.sourceId === id ? null : state.viewer,
        indexProgress,
      };
    }),
  toggleSourceSelected: (id) =>
    set((state) => {
      const selectedSourceIds = new Set(state.selectedSourceIds);
      if (selectedSourceIds.has(id)) selectedSourceIds.delete(id);
      else selectedSourceIds.add(id);
      return { selectedSourceIds };
    }),
  setAllSourcesSelected: (selected) =>
    set((state) => ({
      selectedSourceIds: selected ? new Set(state.sources.map((s) => s.id)) : new Set(),
    })),
  hydrateCachedState: (snapshot) =>
    set((state) => {
      const sourceIds = new Set(state.sources.map((source) => source.id));
      const selectedSourceIds =
        snapshot.selectedSourceIds === undefined
          ? state.selectedSourceIds
          : new Set(snapshot.selectedSourceIds.filter((id) => sourceIds.has(id)));
      const viewer =
        snapshot.viewer && sourceIds.has(snapshot.viewer.sourceId) ? snapshot.viewer : state.viewer;
      const indexProgress =
        snapshot.indexProgress === undefined
          ? state.indexProgress
          : Object.fromEntries(
              Object.entries(snapshot.indexProgress).filter(
                ([id, progress]) => sourceIds.has(id) && progress.source_id === id,
              ),
            );

      return {
        selectedSourceIds,
        viewer,
        centerTab: snapshot.centerTab ?? state.centerTab,
        artifacts: snapshot.artifacts ?? state.artifacts,
        indexProgress,
      };
    }),

  openSource: (id) => set({ viewer: { sourceId: id }, centerTab: "뷰어" }),
  openFile: (sourceId, path) => set({ viewer: { sourceId, path }, centerTab: "뷰어" }),
  setCenterTab: (tab) => set({ centerTab: tab }),
  setIndexProgress: (sourceId, progress) =>
    set((state) => ({
      indexProgress: { ...state.indexProgress, [sourceId]: progress },
    })),
  clearIndexProgress: (sourceId) =>
    set((state) => {
      const indexProgress = { ...state.indexProgress };
      delete indexProgress[sourceId];
      return { indexProgress };
    }),
  createArtifact: (artifact) =>
    set((state) => ({
      artifacts: [
        {
          ...artifact,
          id: makeId(),
          createdAt: Date.now(),
          sourceCount: state.selectedSourceIds.size || state.sources.length,
        },
        ...state.artifacts,
      ],
    })),
  addNote: (title = "새 메모", detail = "방금 전") =>
    set((state) => ({
      artifacts: [
        {
          id: makeId(),
          kind: "note",
          title,
          typeLabel: "메모",
          detail,
          icon: "sticky_note_2",
          tint: "grey",
          createdAt: Date.now(),
          sourceCount: state.selectedSourceIds.size || state.sources.length,
        },
        ...state.artifacts,
      ],
    })),
}));

// 파생 셀렉터: 답변 범위 소스 개수.
export const selectScopeCount = (s: WorkspaceStore) => s.selectedSourceIds.size;
