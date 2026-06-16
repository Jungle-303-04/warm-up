"use client";

import { useEffect, useRef, useState } from "react";

import { getNotebook } from "../lib/api";
import { SourceActionsProvider } from "../lib/source-actions";
import { useWorkspace, type WorkspaceCacheSnapshot } from "../lib/store";
import { PANEL_LIMITS, usePanelSizes } from "../lib/use-panel-sizes";
import type { NotebookDetail } from "../lib/types";
import { CenterPanel } from "./center-panel";
import { Icon } from "./icon";
import { SourcesPanel } from "./sources-panel";
import { StudioPanel } from "./studio-panel";
import { TopBar } from "./top-bar";
import { Panel } from "./ui/panel";
import { ResizeHandle } from "./ui/resize-handle";

interface WorkspaceUiCache extends WorkspaceCacheSnapshot {
  leftCollapsed?: boolean;
  rightCollapsed?: boolean;
}

function workspaceCacheKey(notebookId: string) {
  return `repolm.workspace.${notebookId}`;
}

function readWorkspaceCache(notebookId: string): WorkspaceUiCache | null {
  try {
    const raw = localStorage.getItem(workspaceCacheKey(notebookId));
    return raw ? (JSON.parse(raw) as WorkspaceUiCache) : null;
  } catch {
    return null;
  }
}

function writeWorkspaceCache(notebookId: string, cache: WorkspaceUiCache) {
  try {
    localStorage.setItem(workspaceCacheKey(notebookId), JSON.stringify(cache));
  } catch {
    // 캐시 저장 실패는 화면 동작을 막지 않는다.
  }
}

// 노트북 워크스페이스. 진입 시 노트북 상세를 불러와 스토어를 초기화한다.
export function Workspace({ notebookId }: { notebookId: string }) {
  const [notebook, setNotebook] = useState<NotebookDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const initNotebook = useWorkspace((s) => s.initNotebook);
  const hydrateCachedState = useWorkspace((s) => s.hydrateCachedState);
  const selectedSourceIds = useWorkspace((s) => s.selectedSourceIds);
  const indexProgress = useWorkspace((s) => s.indexProgress);
  const selectedFilePaths = useWorkspace((s) => s.selectedFilePaths);
  const viewer = useWorkspace((s) => s.viewer);
  const centerTab = useWorkspace((s) => s.centerTab);
  const loadArtifacts = useWorkspace((s) => s.loadArtifacts);

  // 3패널 리사이즈: 좌/우 px 너비 상태 + 드래그/키보드 조절.
  const { sizes, setLeft, setRight } = usePanelSizes();
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const mainRef = useRef<HTMLElement | null>(null);
  // 드래그 시작 시점의 기준 너비 스냅샷.
  const baseRef = useRef({ left: sizes.left, right: sizes.right });

  // 가운데 최소폭(360)을 보장하는 좌/우 상한. 컨테이너 폭 기준으로 동적 계산.
  const maxLeftByCenter = () => {
    const w = mainRef.current?.clientWidth ?? Infinity;
    // 핸들 2개(w-1.5≈6px) + gap 4개(gap-3=12px*?) 은 근사 무시, 여유분 24px 차감.
    return Math.max(PANEL_LIMITS.leftMin, w - sizes.right - PANEL_LIMITS.centerMin - 24);
  };
  const maxRightByCenter = () => {
    const w = mainRef.current?.clientWidth ?? Infinity;
    return Math.max(PANEL_LIMITS.rightMin, w - sizes.left - PANEL_LIMITS.centerMin - 24);
  };

  useEffect(() => {
    let active = true;
    setLoading(true);
    getNotebook(notebookId)
      .then((detail) => {
        if (!active) return;
        const cache = readWorkspaceCache(detail.id);
        initNotebook(detail.id, detail.sources);
        // 산출물은 캐시 대신 백엔드 GET 으로 매번 로드(소스 오브 트루스).
        void loadArtifacts(detail.id);
        if (cache) {
          hydrateCachedState(cache);
          setLeftCollapsed(Boolean(cache.leftCollapsed));
          setRightCollapsed(Boolean(cache.rightCollapsed));
        } else {
          setLeftCollapsed(false);
          setRightCollapsed(false);
        }
        setNotebook(detail);
      })
      .catch((e) => active && setError(e instanceof Error ? e.message : "불러오기 실패"))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [hydrateCachedState, initNotebook, loadArtifacts, notebookId]);

  useEffect(() => {
    if (!notebook) return;
    writeWorkspaceCache(notebook.id, {
      selectedSourceIds: [...selectedSourceIds],
      viewer,
      centerTab,
      indexProgress,
      // Set은 JSON 직렬화가 안 되므로 배열로 변환해 저장한다.
      selectedFilePaths: Object.fromEntries(
        Object.entries(selectedFilePaths).map(([id, paths]) => [id, [...paths]]),
      ),
      leftCollapsed,
      rightCollapsed,
    });
  }, [
    centerTab,
    indexProgress,
    leftCollapsed,
    notebook,
    rightCollapsed,
    selectedFilePaths,
    selectedSourceIds,
    viewer,
  ]);

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
    // relative: 모달(absolute inset-0)이 화면 전체를 덮을 기준점.
    <SourceActionsProvider notebookId={notebook.id}>
      <div className="relative flex h-screen flex-col bg-background text-foreground">
        <TopBar notebookId={notebook.id} notebookTitle={notebook.title} />
        <main ref={mainRef} className="flex flex-1 gap-3 overflow-hidden px-3 pb-3 pt-1.5">
          {/* 좌 패널: 동적 px 너비(불가피한 값 → style). */}
          {leftCollapsed ? (
            <CollapsedPanelRail
              side="left"
              label="소스"
              icon="folder"
              onOpen={() => setLeftCollapsed(false)}
            />
          ) : (
            <SourcesPanel
              notebookId={notebook.id}
              style={{ width: `${sizes.left}px` }}
              onCollapse={() => setLeftCollapsed(true)}
            />
          )}

          {/* 좌-중 드래그 핸들 */}
          {leftCollapsed ? null : (
            <ResizeHandle
              ariaLabel="소스 패널 너비 조절"
              onResizeStart={() => {
                baseRef.current.left = sizes.left;
              }}
              onResize={(delta) =>
                setLeft(Math.min(baseRef.current.left + delta, maxLeftByCenter()))
              }
            />
          )}

          {/* 가운데: 나머지 채움 */}
          <CenterPanel />

          {/* 중-우 드래그 핸들(우 패널은 왼쪽으로 끌면 넓어지므로 delta 부호 반전) */}
          {rightCollapsed ? null : (
            <ResizeHandle
              ariaLabel="스튜디오 패널 너비 조절"
              onResizeStart={() => {
                baseRef.current.right = sizes.right;
              }}
              onResize={(delta) =>
                setRight(Math.min(baseRef.current.right - delta, maxRightByCenter()))
              }
            />
          )}

          {/* 우 패널: 동적 px 너비 */}
          {rightCollapsed ? (
            <CollapsedPanelRail
              side="right"
              label="스튜디오"
              icon="auto_awesome"
              onOpen={() => setRightCollapsed(false)}
            />
          ) : (
            <StudioPanel
              style={{ width: `${sizes.right}px` }}
              onCollapse={() => setRightCollapsed(true)}
            />
          )}
        </main>
      </div>
    </SourceActionsProvider>
  );
}

function CollapsedPanelRail({
  side,
  label,
  icon,
  onOpen,
}: {
  side: "left" | "right";
  label: string;
  icon: string;
  onOpen: () => void;
}) {
  return (
    <Panel as="aside" className="w-12 shrink-0">
      <button
        type="button"
        onClick={onOpen}
        title={`${label} 패널 열기`}
        aria-label={`${label} 패널 열기`}
        className="interactive flex h-full w-full flex-col items-center gap-3 px-2 py-3.5 text-muted-foreground hover:bg-secondary hover:text-foreground"
      >
        <Icon name={side === "left" ? "dock_left_open" : "dock_right_open"} size={17} />
        {/* 접힘 레일은 세로 라벨 텍스트 없이 아이콘만 표시(라벨은 title/aria-label로만 제공). */}
        <span className="grid h-8 w-8 place-items-center rounded-xl bg-accent text-accent-foreground">
          <Icon name={icon} size={17} />
        </span>
      </button>
    </Panel>
  );
}
