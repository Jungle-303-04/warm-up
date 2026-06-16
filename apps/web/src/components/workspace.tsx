"use client";

import { useEffect, useRef, useState } from "react";

import { getNotebook } from "../lib/api";
import { useWorkspace } from "../lib/store";
import { PANEL_LIMITS, usePanelSizes } from "../lib/use-panel-sizes";
import type { NotebookDetail } from "../lib/types";
import { CenterPanel } from "./center-panel";
import { Icon } from "./icon";
import { SourcesPanel } from "./sources-panel";
import { StudioPanel } from "./studio-panel";
import { TopBar } from "./top-bar";
import { ResizeHandle } from "./ui/resize-handle";

// 노트북 워크스페이스. 진입 시 노트북 상세를 불러와 스토어를 초기화한다.
export function Workspace({ notebookId }: { notebookId: string }) {
  const [notebook, setNotebook] = useState<NotebookDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const initNotebook = useWorkspace((s) => s.initNotebook);

  // 3패널 리사이즈: 좌/우 px 너비 상태 + 드래그/키보드 조절.
  const { sizes, setLeft, setRight } = usePanelSizes();
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
      <main ref={mainRef} className="flex flex-1 gap-3 overflow-hidden px-3 pb-3 pt-0.5">
        {/* 좌 패널: 동적 px 너비(불가피한 값 → style). */}
        <SourcesPanel notebookId={notebook.id} style={{ width: `${sizes.left}px` }} />

        {/* 좌-중 드래그 핸들 */}
        <ResizeHandle
          ariaLabel="소스 패널 너비 조절"
          onResizeStart={() => {
            baseRef.current.left = sizes.left;
          }}
          onResize={(delta) =>
            setLeft(Math.min(baseRef.current.left + delta, maxLeftByCenter()))
          }
        />

        {/* 가운데: 나머지 채움 */}
        <CenterPanel />

        {/* 중-우 드래그 핸들(우 패널은 왼쪽으로 끌면 넓어지므로 delta 부호 반전) */}
        <ResizeHandle
          ariaLabel="스튜디오 패널 너비 조절"
          onResizeStart={() => {
            baseRef.current.right = sizes.right;
          }}
          onResize={(delta) =>
            setRight(Math.min(baseRef.current.right - delta, maxRightByCenter()))
          }
        />

        {/* 우 패널: 동적 px 너비 */}
        <StudioPanel style={{ width: `${sizes.right}px` }} />
      </main>
    </div>
  );
}
