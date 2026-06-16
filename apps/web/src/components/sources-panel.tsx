"use client";

import { useMemo, useRef, useState } from "react";

import { createSource } from "../lib/api";
import { cn } from "../lib/cn";
import { fileToSourceCreate } from "../lib/file-source";
import { SOURCE_KINDS } from "../lib/fixtures";
import { useWorkspace } from "../lib/store";
import type { SourceKind } from "../lib/types";
import { Icon } from "./icon";
import { SourceAddModal } from "./source-add-modal";
import { SourceRow } from "./source-row";
import { Panel } from "./ui/panel";

// 그룹 표시 순서(종류별 묶음). SOURCE_KINDS에 없는 종류는 무시.
const KIND_ORDER: SourceKind[] = ["repo", "md", "pdf", "text", "url"];

export function SourcesPanel({
  notebookId,
  style,
}: {
  notebookId: string;
  style?: React.CSSProperties;
}) {
  const [addOpen, setAddOpen] = useState(false); // URL·레포 모달
  const sources = useWorkspace((s) => s.sources);
  const addSource = useWorkspace((s) => s.addSource);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  // 드래그 깜빡임 방지용 enter/leave 카운터.
  const dragDepth = useRef(0);
  const [dragActive, setDragActive] = useState(false);
  const [busy, setBusy] = useState(false); // 파일 처리 중
  const [error, setError] = useState<string | null>(null);
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

  const toggleGroup = (kind: SourceKind) =>
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(kind)) next.delete(kind);
      else next.add(kind);
      return next;
    });

  // 파일 목록을 순차 처리 → 각각 createSource → 스토어 반영. 실패는 모아서 표시.
  const processFiles = async (files: FileList | File[]) => {
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
  };

  // 파일 선택창에서 고른 파일 처리.
  const onPick = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) await processFiles(e.target.files);
    e.target.value = ""; // 같은 파일 재선택 허용
  };

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
    <Panel
      as="aside"
      className="relative shrink-0"
      style={style}
    >
      <div
        className="flex min-h-0 flex-1 flex-col"
        onDragEnter={onDragEnter}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        {/* 헤더 */}
        <div className="flex items-center justify-between px-4 pt-4 pb-1">
          <h2 className="text-[15px] font-semibold tracking-tight">소스</h2>
          {sources.length > 0 ? (
            <span className="rounded-full bg-secondary px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
              {sources.length}
            </span>
          ) : null}
        </div>

        {/* 액션: 파일 선택(주) + URL·레포(보조) */}
        <div className="flex gap-2 px-4 pb-2 pt-1">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="interactive flex flex-1 items-center justify-center gap-2 rounded-full border border-border bg-card px-4 py-2.5 text-[13px] font-medium text-foreground hover:bg-secondary hover:shadow-elev-1 active:scale-[0.99]"
          >
            <Icon name="add" size={18} className="text-primary" />
            소스 추가
          </button>
          <button
            type="button"
            onClick={() => setAddOpen(true)}
            title="URL · GitHub 레포 추가"
            aria-label="URL · 레포 추가"
            className="interactive grid h-[42px] w-[42px] shrink-0 place-items-center rounded-full border border-border bg-card text-muted-foreground hover:bg-secondary hover:text-foreground hover:shadow-elev-1 active:scale-[0.97]"
          >
            <Icon name="link" size={18} />
          </button>
        </div>

        {/* 시각적으로 숨긴 파일 input(버튼으로 트리거) */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.md,.markdown,.txt,text/plain,text/markdown,application/pdf"
          className="hidden"
          onChange={onPick}
        />

        {/* 검색/디스커버: 소스 이름 필터(실제 동작) */}
        {sources.length > 0 ? (
          <div className="px-4 pb-2 pt-1">
            <div className="interactive flex items-center gap-2 rounded-full border border-border bg-secondary/60 px-3.5 py-2 focus-within:border-primary/50 focus-within:bg-card">
              <Icon name="travel_explore" size={16} className="shrink-0 text-muted-foreground" />
              <input
                type="text"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                placeholder="소스에서 검색…"
                aria-label="소스 검색"
                className="min-w-0 flex-1 bg-transparent text-[13px] outline-none placeholder:text-muted-foreground"
              />
              {filter ? (
                <button
                  type="button"
                  onClick={() => setFilter("")}
                  aria-label="검색 지우기"
                  className="interactive grid h-5 w-5 shrink-0 place-items-center rounded-full text-muted-foreground hover:bg-secondary hover:text-foreground"
                >
                  <Icon name="close" size={13} />
                </button>
              ) : null}
            </div>
          </div>
        ) : null}

        {/* 처리 상태 / 에러 */}
        {busy ? (
          <p className="mx-4 mb-1 flex items-center gap-1.5 text-[12px] text-muted-foreground">
            <Icon name="progress_activity" size={13} className="animate-spin" />
            파일 처리 중…
          </p>
        ) : null}
        {error ? <p className="mx-4 mb-1 text-[12px] text-destructive">{error}</p> : null}

        <div className="scroll-thin flex-1 overflow-y-auto px-2 pb-3 pt-1">
          {sources.length === 0 ? (
            <div className="mt-10 px-4 text-center">
              <span className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-accent text-accent-foreground">
                <Icon name="description" size={26} />
              </span>
              <p className="mt-4 text-[14px] font-semibold">저장된 소스가 없습니다</p>
              <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted-foreground">
                PDF·문서·텍스트 파일을 여기로 끌어다 놓거나 “소스 추가”로 선택하세요.
              </p>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="interactive mt-4 inline-flex items-center gap-1.5 rounded-full bg-primary px-4 py-2 text-[13px] font-medium text-primary-foreground hover:opacity-90 active:scale-[0.98]"
              >
                <Icon name="add" size={16} /> 첫 소스 추가
              </button>
            </div>
          ) : (
            <>
              {/* 자동 포함 안내(체크박스 없음) */}
              <div className="mx-1 mb-1 flex items-start gap-1.5 rounded-lg px-2 py-1.5 text-[11.5px] leading-snug text-muted-foreground">
                <Icon name="check_circle" size={13} className="mt-0.5 shrink-0 text-primary" />
                <span>모든 소스가 자동으로 답변 근거에 포함됩니다.</span>
              </div>

              {filteredEmpty ? (
                <p className="mt-6 px-4 text-center text-[12.5px] text-muted-foreground">
                  “{filter.trim()}”와 일치하는 소스가 없습니다.
                </p>
              ) : (
                <div className="space-y-2">
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
                            className="interactive flex w-full items-center gap-1.5 rounded-md px-2 py-1.5 text-left text-[11.5px] font-medium uppercase tracking-wide text-muted-foreground hover:bg-secondary"
                          >
                            <Icon
                              name="chevron_right"
                              size={13}
                              className={cn("shrink-0 transition-transform", isOpen && "rotate-90")}
                            />
                            <span className="flex-1 normal-case tracking-normal">{cfg.label}</span>
                            <span className="rounded-full bg-secondary px-1.5 py-0.5 text-[10px] font-semibold normal-case tracking-normal">
                              {g.items.length}
                            </span>
                          </button>
                        )}
                        {isOpen ? (
                          <div className={cn("space-y-0.5", singleKind ? "" : "mt-0.5")}>
                            {g.items.map((s) => (
                              <SourceRow key={s.id} source={s} notebookId={notebookId} />
                            ))}
                          </div>
                        ) : null}
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
            <span className="grid h-12 w-12 place-items-center rounded-2xl bg-primary text-primary-foreground">
              <Icon name="upload_file" size={24} />
            </span>
            <p className="text-[14px] font-semibold">여기에 놓아 소스로 추가</p>
            <p className="text-[12px] opacity-80">PDF · Markdown · 텍스트</p>
          </div>
        ) : null}
      </div>

      <SourceAddModal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        notebookId={notebookId}
      />
    </Panel>
  );
}
