"use client";

import { useMemo, useRef, useState } from "react";

import { cn } from "../lib/cn";
import { SOURCE_KINDS } from "../lib/fixtures";
import { useSourceActions } from "../lib/source-actions";
import { useWorkspace } from "../lib/store";
import type { SourceKind } from "../lib/types";
import { Icon } from "./icon";
import { SourceRow } from "./source-row";
import { Button } from "./ui/button";
import { Collapse } from "./ui/collapse";
import { Panel } from "./ui/panel";

// 그룹 표시 순서(종류별 묶음). SOURCE_KINDS에 없는 종류는 무시.
const KIND_ORDER: SourceKind[] = ["repo", "md", "pdf", "text", "url"];

export function SourcesPanel({
  notebookId,
  style,
  onCollapse,
}: {
  notebookId: string;
  style?: React.CSSProperties;
  onCollapse?: () => void;
}) {
  const sources = useWorkspace((s) => s.sources);
  const selectedCount = useWorkspace((s) => s.selectedSourceIds.size);
  const setAllSourcesSelected = useWorkspace((s) => s.setAllSourcesSelected);
  // 소스 추가 흐름은 공용 컨텍스트에서 가져온다(온보딩 히어로와 공유).
  // 파일/URL/GitHub는 단일 "소스 추가" 모달로 일원화됐다.
  const { openAddSource, busy, error, processFiles } = useSourceActions();

  // 드래그 깜빡임 방지용 enter/leave 카운터.
  const dragDepth = useRef(0);
  const [dragActive, setDragActive] = useState(false);
  const [filter, setFilter] = useState(""); // 소스 이름 필터
  // 접힌 그룹 키 집합(기본 모두 펼침).
  const [collapsed, setCollapsed] = useState<Set<SourceKind>>(new Set());

  // 이름 필터 적용 → 종류별 그룹화. KIND_ORDER 순서로 정렬.
  const groups = useMemo(() => {
    const q = filter.trim().toLowerCase();
    const matched = q
      ? sources.filter((s) => s.title.toLowerCase().includes(q))
      : sources;
    return KIND_ORDER.map((kind) => ({
      kind,
      items: matched.filter((s) => s.kind === kind),
    })).filter((g) => g.items.length > 0);
  }, [sources, filter]);

  // 종류가 한 가지뿐이면 그룹 헤더 생략.
  const singleKind = groups.length <= 1;
  const filteredEmpty = filter.trim().length > 0 && groups.length === 0;
  const empty = sources.length === 0;
  const allSelected = sources.length > 0 && selectedCount === sources.length;
  const someSelected = selectedCount > 0 && selectedCount < sources.length;

  const toggleGroup = (kind: SourceKind) =>
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(kind)) next.delete(kind);
      else next.add(kind);
      return next;
    });

  // ── 드래그앤드롭 핸들러(카운팅으로 깜빡임 방지) ───────────────────
  const onDragEnter = (e: React.DragEvent) => {
    if (!e.dataTransfer.types.includes("Files")) return;
    e.preventDefault();
    dragDepth.current += 1;
    setDragActive(true);
  };
  const onDragOver = (e: React.DragEvent) => {
    if (!e.dataTransfer.types.includes("Files")) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = "copy";
  };
  const onDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    dragDepth.current -= 1;
    if (dragDepth.current <= 0) {
      dragDepth.current = 0;
      setDragActive(false);
    }
  };
  const onDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    dragDepth.current = 0;
    setDragActive(false);
    if (e.dataTransfer.files?.length) await processFiles(e.dataTransfer.files);
  };

  return (
    <Panel as="aside" className="relative shrink-0" style={style}>
      <div
        className="flex min-h-0 flex-1 flex-col"
        onDragEnter={onDragEnter}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        {/* 헤더 */}
        <div className="flex h-11 items-center justify-between border-b border-border px-3">
          <div className="flex items-center gap-1.5">
            <Icon name="folder" size={16} className="text-muted-foreground" />
            <h2 className="t-title">소스</h2>
          </div>
          <div className="flex items-center gap-1.5">
            {sources.length > 0 ? (
              <span className="rounded-full bg-secondary px-2 py-0.5 text-[11px] font-semibold tabular-nums text-muted-foreground">
                {selectedCount}/{sources.length}
              </span>
            ) : null}
            {onCollapse ? (
              <button
                type="button"
                onClick={onCollapse}
                title="소스 패널 접기"
                aria-label="소스 패널 접기"
                className="transition-all duration-200 ease-in-out grid h-7 w-7 place-items-center rounded-full text-muted-foreground hover:bg-secondary hover:text-foreground"
              >
                <Icon name="dock_to_left" size={15} />
              </button>
            ) : null}
          </div>
        </div>

        {/* 액션: 단일 "소스 추가" 진입점(통합 모달 → 파일·URL·GitHub). 공용 sm 알약. */}
        <div className="px-3 pb-2 pt-2.5">
          <Button
            variant="primary"
            size="sm"
            icon="add"
            onClick={openAddSource}
            className="w-full"
          >
            소스 추가
          </Button>
        </div>

        {/* 검색: 소스 이름 필터(소스 0개면 비활성 placeholder). 밀도에 맞춰 단정하게 축소. */}
        <div className="px-3 pb-2">
          <div
            className={cn(
              "transition-all duration-200 ease-in-out flex items-center gap-1.5 rounded-full border border-border px-2.5 py-1",
              empty
                ? "bg-secondary/40 opacity-60"
                : "bg-secondary/60 focus-within:border-primary/50 focus-within:bg-card",
            )}
          >
            <Icon name="travel_explore" size={12} className="shrink-0 text-muted-foreground" />
            <input
              type="text"
              value={filter}
              disabled={empty}
              onChange={(e) => setFilter(e.target.value)}
              placeholder={empty ? "소스를 추가하면 검색할 수 있어요" : "소스에서 검색…"}
              aria-label="소스 검색"
              className="min-w-0 flex-1 bg-transparent text-[12px] font-medium leading-4 outline-none placeholder:font-normal placeholder:text-muted-foreground disabled:cursor-not-allowed"
            />
            {filter ? (
              <button
                type="button"
                onClick={() => setFilter("")}
                aria-label="검색 지우기"
                className="transition-all duration-200 ease-in-out grid h-4 w-4 shrink-0 place-items-center rounded-full text-muted-foreground hover:bg-secondary hover:text-foreground"
              >
                <Icon name="close" size={12} />
              </button>
            ) : null}
          </div>
        </div>

        {/* 처리 상태 / 에러: 급격한 표시 대신 height/opacity로 부드럽게 여닫는다. */}
        <Collapse open={busy}>
          <p className="mx-3 mb-1 flex items-center gap-1.5 text-[11.5px] text-muted-foreground">
            <Icon name="progress_activity" size={12} className="animate-spin" />
            파일 처리 중…
          </p>
        </Collapse>
        <Collapse open={!!error}>
          <p className="mx-3 mb-1 text-[11.5px] text-destructive">{error}</p>
        </Collapse>

        <div className="flex-1 overflow-y-auto px-2 pb-3 pt-1">
          {empty ? (
            <div className="mt-7 px-4 text-center">
              <span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-accent text-accent-foreground shadow-sm">
                <Icon name="upload_file" size={24} />
              </span>
              <p className="mt-3.5 text-[13px] font-semibold">아직 소스가 없어요</p>
              <p className="mt-1.5 text-[12px] leading-relaxed text-muted-foreground">
                파일을 여기로 끌어다 놓거나
                <br />
                위의 버튼으로 소스를 추가하세요.
              </p>
              {/* 끌어다 놓기 힌트(점선존) → 통합 소스 추가 모달 */}
              <button
                type="button"
                onClick={openAddSource}
                className="transition-all duration-200 ease-in-out mt-3.5 flex w-full flex-col items-center gap-1.5 rounded-xl border-2 border-dashed border-border px-4 py-4 text-muted-foreground hover:border-primary/40 hover:bg-secondary/50 hover:text-foreground"
              >
                <Icon name="add" size={18} className="text-primary" />
                <span className="text-[12px] font-medium">파일 · URL · GitHub 추가</span>
              </button>
            </div>
          ) : (
            <>
              <label className="transition-all duration-200 ease-in-out mx-1 mb-1 flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-[11px] text-muted-foreground hover:bg-secondary">
                <span className="relative grid h-4 w-4 place-items-center rounded-[4px] border border-input bg-card">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    ref={(el) => {
                      if (el) el.indeterminate = someSelected;
                    }}
                    onChange={(e) => setAllSourcesSelected(e.target.checked)}
                    aria-label="모든 소스 선택"
                    className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
                  />
                  {allSelected ? (
                    <span className="absolute inset-[-1px] grid place-items-center rounded-[4px] bg-primary text-primary-foreground">
                      <Icon name="check" size={12} strokeWidth={2.5} />
                    </span>
                  ) : someSelected ? (
                    <span className="h-2 w-2 rounded-[2px] bg-primary" />
                  ) : null}
                </span>
                <span className="flex-1 font-medium text-foreground">모두 선택</span>
                <span className="tabular-nums">{selectedCount}개</span>
              </label>

              {filteredEmpty ? (
                <p className="mt-5 px-4 text-center text-[12px] text-muted-foreground">
                  “{filter.trim()}”와 일치하는 소스가 없습니다.
                </p>
              ) : (
                <div className="space-y-1.5">
                  {groups.map((g) => {
                    const cfg = SOURCE_KINDS[g.kind];
                    const isOpen = !collapsed.has(g.kind);
                    return (
                      <div key={g.kind}>
                        {/* 그룹 헤더: 종류 라벨 + 개수 + chevron(접기/펴기). 단일 종류면 생략 */}
                        {singleKind ? null : (
                          <button
                            type="button"
                            onClick={() => toggleGroup(g.kind)}
                            className="transition-all duration-200 ease-in-out flex w-full items-center gap-1.5 rounded-md px-2 py-1 text-left text-[11px] font-semibold uppercase tracking-normal text-muted-foreground hover:bg-secondary"
                          >
                            <Icon
                              name="chevron_right"
                              size={12}
                              className={cn("shrink-0 transition-transform", isOpen && "rotate-90")}
                            />
                            <span className="flex-1 normal-case tracking-normal">{cfg.label}</span>
                            <span className="rounded-full bg-secondary px-1.5 py-0.5 text-[10px] font-semibold normal-case tracking-normal">
                              {g.items.length}
                            </span>
                          </button>
                        )}
                        <Collapse open={isOpen}>
                          <div className={cn("space-y-px", singleKind ? "" : "mt-0.5")}>
                            {g.items.map((s) => (
                              <SourceRow key={s.id} source={s} notebookId={notebookId} />
                            ))}
                          </div>
                        </Collapse>
                      </div>
                    );
                  })}
                </div>
              )}
            </>
          )}
        </div>

        {/* 드롭 오버레이: 파일 드래그 중에만 표시 */}
        {dragActive ? (
          <div
            aria-hidden
            className={cn(
              "pointer-events-none absolute inset-0 z-10 m-2 flex flex-col items-center justify-center gap-2 rounded-[12px]",
              "border-2 border-dashed border-primary bg-accent/85 text-accent-foreground backdrop-blur-sm",
            )}
          >
            <span className="grid h-11 w-11 place-items-center rounded-2xl bg-primary text-primary-foreground">
              <Icon name="upload_file" size={22} />
            </span>
            <p className="text-[13px] font-semibold">여기에 놓아 소스로 추가</p>
            <p className="text-[11.5px] opacity-80">PDF · Markdown · 텍스트</p>
          </div>
        ) : null}
      </div>
    </Panel>
  );
}
