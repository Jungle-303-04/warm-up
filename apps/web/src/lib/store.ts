"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

import {
  createArtifact as apiCreateArtifact,
  createNote as apiCreateNote,
  createSource as apiCreateSource,
  deleteArtifact as apiDeleteArtifact,
  isMermaidArtifact,
  listArtifacts as apiListArtifacts,
  updateArtifact as apiUpdateArtifact,
} from "./api";
import type {
  Artifact,
  CenterTab,
  GeneratableArtifactType,
  IndexProgress,
  Source,
  SourceKind,
} from "./types";

// 뷰어가 가리키는 대상: 소스 자체, repo 소스 안의 특정 파일, 또는 산출물.
// artifactId 가 있으면 산출물 뷰어, 없으면 (sourceId 기반) 소스/파일 뷰어.
export interface ViewerTarget {
  sourceId?: string;
  // path 가 있으면 repo 파일, 없으면 소스 본문.
  path?: string;
  // 산출물 뷰어 대상(다이어그램/메모). 지정 시 소스/파일 필드는 무시.
  artifactId?: string;
}

export interface WorkspaceCacheSnapshot {
  selectedSourceIds?: string[];
  viewer?: ViewerTarget | null;
  centerTab?: CenterTab;
  // repo 소스별 선택된 파일 경로(답변 범위). 직렬화를 위해 배열로 저장.
  selectedFilePaths?: Record<string, string[]>;
}

// 노트북 화면 전역 상태. 모든 소스는 자동으로 답변 범위에 포함된다(선택 개념 없음).
interface WorkspaceStore {
  notebookId: string | null;
  sources: Source[];
  selectedSourceIds: Set<string>;
  viewer: ViewerTarget | null; // 중앙 뷰어가 여는 대상
  centerTab: CenterTab;
  // 백엔드 산출물 목록(아티팩트/메모). 노트북 진입 시 GET 으로 로드.
  artifacts: Artifact[];
  artifactsLoading: boolean; // 산출물 목록 로딩 중
  artifactsError: string | null; // 산출물 목록/조작 에러
  generatingType: GeneratableArtifactType | null; // 다이어그램 생성 중인 타입(로딩 표시)
  // 소스별 RAG 인덱싱 진행(백엔드 SSE 스냅샷). key = sourceId.
  indexProgress: Record<string, IndexProgress>;
  // repo 소스별 답변 범위에 포함된 파일 경로 집합. key = sourceId.
  // 기본 "전체 선택"이지만, supported 파일 목록을 알아야 하므로 SSE files 도착 시
  // initFilePaths로 채운다. 엔트리가 없으면 "아직 초기화 전(=전체 포함)"으로 본다.
  selectedFilePaths: Record<string, Set<string>>;

  initNotebook: (notebookId: string, sources: Source[]) => void;
  setSources: (sources: Source[]) => void;
  addSource: (source: Source) => void; // 소스 추가 후 목록 반영
  removeSource: (id: string) => void;
  toggleSourceSelected: (id: string) => void;
  setAllSourcesSelected: (selected: boolean) => void;
  // repo 파일 선택: 최초 supported 목록으로 기본 전체 선택 채우기(이미 있으면 무시).
  initFilePaths: (sourceId: string, supportedPaths: string[]) => void;
  toggleFilePath: (sourceId: string, path: string) => void;
  // 소스의 supported 파일을 한 번에 전체 선택/해제(트라이스테이트 헤더용).
  setAllFilePaths: (sourceId: string, supportedPaths: string[], selected: boolean) => void;
  hydrateCachedState: (snapshot: WorkspaceCacheSnapshot) => void;

  openSource: (id: string) => void; // 소스 본문을 뷰어에 열기 + 뷰어 탭으로 이동
  openFile: (sourceId: string, path: string) => void; // repo 파일을 뷰어에 열기
  openArtifact: (id: string) => void; // 산출물을 뷰어에 열기 + 뷰어 탭으로 이동
  setCenterTab: (tab: CenterTab) => void;

  // ── 채팅 컨트롤 신호(센터 바 ↔ 채팅뷰) ──────────────────────────────
  // 탭 바의 버튼이 채팅뷰의 동작을 트리거하는 1회성 신호(nonce). 영속화하지 않는다.
  resetChatSignal: number; // 대화 초기화 요청
  saveChatSignal: number; // 대화를 메모로 저장 요청
  chatMessageCount: number; // 채팅뷰가 공개하는 현재 메시지 수(버튼 활성/비활성용)
  requestResetChat: () => void;
  requestSaveChat: () => void;
  setChatMessageCount: (count: number) => void;
  setIndexProgress: (sourceId: string, progress: IndexProgress) => void;
  clearIndexProgress: (sourceId: string) => void;

  // ── 산출물(백엔드 연동) ──────────────────────────────────────────
  loadArtifacts: (notebookId: string) => Promise<void>; // GET 목록 로드
  // 다이어그램/요약 생성(POST). 성공 시 목록 맨 앞에 추가하고 뷰어로 열며 생성된 산출물을 반환.
  generateArtifact: (type: GeneratableArtifactType, sourceIds: string[]) => Promise<Artifact | null>;
  // 메모 생성(POST note). body(본문)를 content 로 저장.
  addNote: (input?: { title?: string; content?: string }) => Promise<Artifact | null>;
  // 산출물 수정(PATCH). 성공 시 목록·뷰어 반영.
  updateArtifact: (id: string, patch: { title?: string; content?: string }) => Promise<Artifact | null>;
  removeArtifact: (id: string) => Promise<void>; // 삭제(DELETE)
  // 산출물 content 로 새 소스를 만든다(소스로 추가). 성공 시 좌측 소스 목록에 반영(addSource)되고
  // 기존 흐름대로 자동 인덱싱이 진행된다. 생성된 소스를 반환.
  addArtifactAsSource: (artifact: Artifact) => Promise<Source | null>;
}

export const useWorkspace = create<WorkspaceStore>()(
  persist(
    (set, get) => ({
      notebookId: null,
      sources: [],
      selectedSourceIds: new Set(),
      viewer: null,
      centerTab: "대화",
      artifacts: [],
      artifactsLoading: false,
      artifactsError: null,
      generatingType: null,
      indexProgress: {},
      selectedFilePaths: {},
      resetChatSignal: 0,
      saveChatSignal: 0,
      chatMessageCount: 0,

      initNotebook: (notebookId, sources) =>
        set({
          notebookId,
          sources,
          selectedSourceIds: new Set(sources.map((s) => s.id)),
          viewer: null,
          centerTab: "대화",
          indexProgress: {},
          selectedFilePaths: {},
          // 산출물은 loadArtifacts(백엔드 GET)로 채운다. 진입 시 초기화.
          artifacts: [],
          artifactsLoading: false,
          artifactsError: null,
          generatingType: null,
        }),
      setSources: (sources) =>
        set((state) => {
          const nextSourceIds = new Set(sources.map((source) => source.id));
          // 사라진 소스의 진행 상태는 정리한다.
          const indexProgress: Record<string, IndexProgress> = {};
          for (const [id, progress] of Object.entries(state.indexProgress)) {
            if (nextSourceIds.has(id)) indexProgress[id] = progress;
          }
          // 사라진 소스의 파일 선택 상태도 정리한다.
          const selectedFilePaths: Record<string, Set<string>> = {};
          for (const [id, paths] of Object.entries(state.selectedFilePaths)) {
            if (nextSourceIds.has(id)) selectedFilePaths[id] = paths;
          }

          return {
            sources,
            selectedSourceIds: new Set(
              sources
                .map((s) => s.id)
                .filter((id) => state.selectedSourceIds.has(id) || state.selectedSourceIds.size === 0),
            ),
            indexProgress,
            selectedFilePaths,
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
          const selectedFilePaths = { ...state.selectedFilePaths };
          delete selectedFilePaths[id];
          return {
            sources: state.sources.filter((s) => s.id !== id),
            selectedSourceIds,
            viewer: state.viewer?.sourceId === id ? null : state.viewer,
            indexProgress,
            selectedFilePaths,
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
      initFilePaths: (sourceId, supportedPaths) =>
        set((state) => {
          // 이미 초기화된 소스는 사용자의 선택을 보존(덮어쓰지 않음).
          if (state.selectedFilePaths[sourceId]) return {};
          return {
            selectedFilePaths: {
              ...state.selectedFilePaths,
              [sourceId]: new Set(supportedPaths),
            },
          };
        }),
      toggleFilePath: (sourceId, path) =>
        set((state) => {
          const current = state.selectedFilePaths[sourceId] ?? new Set<string>();
          const next = new Set(current);
          if (next.has(path)) next.delete(path);
          else next.add(path);
          return {
            selectedFilePaths: { ...state.selectedFilePaths, [sourceId]: next },
          };
        }),
      setAllFilePaths: (sourceId, supportedPaths, selected) =>
        set((state) => ({
          selectedFilePaths: {
            ...state.selectedFilePaths,
            [sourceId]: selected ? new Set(supportedPaths) : new Set<string>(),
          },
        })),
      hydrateCachedState: (snapshot) =>
        set((state) => {
          const sourceIds = new Set(state.sources.map((source) => source.id));
          const selectedSourceIds =
            snapshot.selectedSourceIds === undefined
              ? state.selectedSourceIds
              : new Set(snapshot.selectedSourceIds.filter((id) => sourceIds.has(id)));
          // 캐시된 뷰어 대상 복원: 산출물 뷰어는 그대로, 소스/파일 뷰어는 소스 존재 시에만.
          const cachedViewer = snapshot.viewer;
          const viewer = cachedViewer
            ? cachedViewer.artifactId
              ? cachedViewer
              : cachedViewer.sourceId && sourceIds.has(cachedViewer.sourceId)
                ? cachedViewer
                : state.viewer
            : state.viewer;
          const selectedFilePaths =
            snapshot.selectedFilePaths === undefined
              ? state.selectedFilePaths
              : Object.fromEntries(
                  Object.entries(snapshot.selectedFilePaths)
                    .filter(([id]) => sourceIds.has(id))
                    .map(([id, paths]) => [id, new Set(paths)]),
                );

          return {
            selectedSourceIds,
            viewer,
            centerTab: snapshot.centerTab ?? state.centerTab,
            selectedFilePaths,
          };
        }),

      openSource: (id) => set({ viewer: { sourceId: id }, centerTab: "뷰어" }),
      openFile: (sourceId, path) => set({ viewer: { sourceId, path }, centerTab: "뷰어" }),
      openArtifact: (id) => set({ viewer: { artifactId: id }, centerTab: "뷰어" }),
      setCenterTab: (tab) => set({ centerTab: tab }),
      requestResetChat: () => set((state) => ({ resetChatSignal: state.resetChatSignal + 1 })),
      requestSaveChat: () => set((state) => ({ saveChatSignal: state.saveChatSignal + 1 })),
      setChatMessageCount: (count) => set({ chatMessageCount: count }),
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
      // ── 산출물(백엔드 연동) ──────────────────────────────────────────
      loadArtifacts: async (notebookId) => {
        set({ artifactsLoading: true, artifactsError: null });
        try {
          const { artifacts } = await apiListArtifacts(notebookId);
          // 진입한 노트북이 그대로일 때만 반영(경합 방지).
          if (get().notebookId !== notebookId) return;
          set({ artifacts, artifactsLoading: false });
        } catch (error) {
          if (get().notebookId !== notebookId) return;
          set({
            artifactsLoading: false,
            artifactsError: error instanceof Error ? error.message : "산출물을 불러오지 못했습니다",
          });
        }
      },

      generateArtifact: async (type, sourceIds) => {
        const { notebookId } = get();
        if (!notebookId) return null;
        if (sourceIds.length === 0) {
          set({ artifactsError: "선택된 소스가 없어 산출물을 생성할 수 없습니다" });
          return null;
        }
        set({ generatingType: type, artifactsError: null });
        try {
          const created = await apiCreateArtifact(notebookId, {
            type,
            source_ids: sourceIds,
          });
          set((state) => ({
            artifacts: [created, ...state.artifacts],
            generatingType: null,
            viewer: { artifactId: created.id },
            centerTab: "뷰어",
          }));
          return created;
        } catch (error) {
          set({
            generatingType: null,
            artifactsError: error instanceof Error ? error.message : "산출물 생성 실패",
          });
          return null;
        }
      },

      addNote: async (input) => {
        const { notebookId } = get();
        if (!notebookId) return null;
        try {
          const created = await apiCreateNote(notebookId, {
            title: input?.title,
            content: input?.content ?? "",
          });
          set((state) => ({ artifacts: [created, ...state.artifacts], artifactsError: null }));
          return created;
        } catch (error) {
          set({
            artifactsError: error instanceof Error ? error.message : "메모 생성 실패",
          });
          return null;
        }
      },

      updateArtifact: async (id, patch) => {
        const { notebookId } = get();
        if (!notebookId) return null;
        try {
          const updated = await apiUpdateArtifact(notebookId, id, patch);
          set((state) => ({
            artifacts: state.artifacts.map((a) => (a.id === id ? updated : a)),
            artifactsError: null,
          }));
          return updated;
        } catch (error) {
          set({
            artifactsError: error instanceof Error ? error.message : "산출물 수정 실패",
          });
          return null;
        }
      },

      addArtifactAsSource: async (artifact) => {
        const { notebookId } = get();
        if (!notebookId) return null;
        // Mermaid 다이어그램(uml/erd/dependency)은 텍스트 소스로, 마크다운(note/change_summary)은 md 소스로 추가.
        const kind: SourceKind = isMermaidArtifact(artifact.type) ? "text" : "md";
        try {
          const source = await apiCreateSource(notebookId, {
            kind,
            title: artifact.title,
            content: artifact.content,
            derived_from_artifact_id: artifact.id,
            lineage_source_ids: artifact.source_ids,
          });
          // 좌측 소스 목록에 반영 → 기존 흐름대로 자동 인덱싱이 진행된다.
          get().addSource(source);
          set({ artifactsError: null });
          return source;
        } catch (error) {
          set({
            artifactsError: error instanceof Error ? error.message : "소스로 추가 실패",
          });
          return null;
        }
      },

      removeArtifact: async (id) => {
        const { notebookId } = get();
        if (!notebookId) return;
        // 낙관적 제거 + 뷰어가 해당 산출물을 보고 있으면 닫는다.
        const prev = get().artifacts;
        set((state) => ({
          artifacts: state.artifacts.filter((a) => a.id !== id),
          viewer: state.viewer?.artifactId === id ? null : state.viewer,
        }));
        try {
          await apiDeleteArtifact(notebookId, id);
        } catch (error) {
          // 실패 시 롤백.
          set({
            artifacts: prev,
            artifactsError: error instanceof Error ? error.message : "산출물 삭제 실패",
          });
        }
      },
    }),
    {
      name: "repolm-workspace-storage",
      storage: {
        // 직렬화 시 Set→배열, 역직렬화 시 배열→Set로 변환한다.
        // PersistStorage의 엄격한 타입과 충돌하지 않도록 직렬화 경계에서만 느슨한 타입을 쓴다.
        getItem: (name) => {
          const str = localStorage.getItem(name);
          if (!str) return null;
          try {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const data = JSON.parse(str) as { state?: any };
            const s = data.state;
            if (s) {
              if (Array.isArray(s.selectedSourceIds)) {
                s.selectedSourceIds = new Set(s.selectedSourceIds as string[]);
              }
              if (s.selectedFilePaths && typeof s.selectedFilePaths === "object") {
                const selectedFilePaths: Record<string, Set<string>> = {};
                for (const [id, paths] of Object.entries(s.selectedFilePaths)) {
                  selectedFilePaths[id] = new Set(paths as string[]);
                }
                s.selectedFilePaths = selectedFilePaths;
              }
            }
            return data as never;
          } catch {
            return null;
          }
        },
        setItem: (name, value) => {
          // 저장 직전 스냅샷을 평문 직렬화 형태로 복제(Set→배열).
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const state: any = { ...(value.state as any) };
          if (state.selectedSourceIds instanceof Set) {
            state.selectedSourceIds = Array.from(state.selectedSourceIds);
          }
          if (state.selectedFilePaths && typeof state.selectedFilePaths === "object") {
            const selectedFilePaths: Record<string, string[]> = {};
            for (const [id, pathsSet] of Object.entries(state.selectedFilePaths)) {
              selectedFilePaths[id] = pathsSet instanceof Set ? Array.from(pathsSet) : [];
            }
            state.selectedFilePaths = selectedFilePaths;
          }
          localStorage.setItem(name, JSON.stringify({ ...value, state }));
        },
        removeItem: (name) => localStorage.removeItem(name),
      },
      // 영속화 대상만 추린다(나머지는 진입 시 재로딩). persist의 partial 타입과 맞추기 위해 단언.
      partialize: (state) =>
        ({
          notebookId: state.notebookId,
          viewer: state.viewer,
          centerTab: state.centerTab,
          selectedSourceIds: state.selectedSourceIds,
          selectedFilePaths: state.selectedFilePaths,
        }) as WorkspaceStore,
    }
  )
);

// 파생 셀렉터: 답변 범위 소스 개수.
export const selectScopeCount = (s: WorkspaceStore) => s.selectedSourceIds.size;
