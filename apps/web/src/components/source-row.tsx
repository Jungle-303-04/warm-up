"use client";

import { useEffect, useState } from "react";

import { useIndexProgress } from "../hooks/use-index-progress";
import { deleteSource, getTree, reindexSource } from "../lib/api";
import { cn } from "../lib/cn";
import { fileIconForPath, SOURCE_KINDS } from "../lib/fixtures";
import {
  indexFilesByPath,
  isIndexActive,
  isSupportedPath,
  supportedFilePaths,
} from "../lib/indexing";
import { useWorkspace } from "../lib/store";
import type { IndexFile, IndexProgress, Source, TreeNode } from "../lib/types";
import { Icon } from "./icon";
import { SourceIcon } from "./source-icon";

// 정지 의심 판정 임계값(ms). queued/running인데 이 시간 이상 updated_at이
// 갱신되지 않으면 멈춘 것으로 보고 재분석 버튼을 노출한다(너무 공격적이지 않게).
const STALL_THRESHOLD_MS = 20_000;

// last_synced_at(ISO) → "마지막 동기화: YYYY.MM.DD HH:mm" (ko-KR). 파싱 실패 시 null.
function formatLastSynced(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  const fmt = d.toLocaleString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
  // ko-KR는 "2026. 06. 17. 14:30" 형태 → "2026.06.17 14:30"으로 정돈.
  return fmt.replace(/\.\s/g, ".").replace(/\.(\d{2}:\d{2})/, " $1").replace(/\.$/, "");
}

// 파일 단위 인덱싱 상태 → 아이콘/색.
function fileStatusIcon(status: IndexFile["status"]): { icon: string; spin: boolean; className: string } {
  switch (status) {
    case "done":
      return { icon: "check_circle", spin: false, className: "text-primary" };
    case "indexing":
      return { icon: "progress_activity", spin: true, className: "text-primary" };
    case "failed":
      return { icon: "report", spin: false, className: "text-destructive" };
    case "skipped":
      return { icon: "remove", spin: false, className: "text-muted-foreground/60" };
    case "queued":
      return { icon: "schedule", spin: false, className: "text-muted-foreground" };
  }
}

// 작은 체크박스(파일/소스 트라이스테이트 공용). state=checked|unchecked|indeterminate.
function MiniCheckbox({
  state,
  onToggle,
  label,
  title,
}: {
  state: "checked" | "unchecked" | "indeterminate";
  onToggle: () => void;
  label: string;
  title?: string;
}) {
  return (
    <label
      className="interactive grid h-5 w-5 shrink-0 cursor-pointer place-items-center rounded-md"
      title={title}
      onClick={(e) => e.stopPropagation()}
    >
      <input
        type="checkbox"
        checked={state === "checked"}
        ref={(el) => {
          if (el) el.indeterminate = state === "indeterminate";
        }}
        onChange={onToggle}
        aria-label={label}
        className="peer sr-only"
      />
      <span
        aria-hidden
        className={cn(
          "grid h-4 w-4 place-items-center rounded-[4px] border border-input bg-card",
          state === "checked" && "border-primary bg-primary text-primary-foreground",
          state === "indeterminate" && "border-primary bg-card",
        )}
      >
        {state === "checked" ? (
          <Icon name="check" size={12} strokeWidth={2.5} />
        ) : state === "indeterminate" ? (
          <span className="h-2 w-2 rounded-[2px] bg-primary" />
        ) : null}
      </span>
    </label>
  );
}

// 재귀 파일 트리. 디렉터리는 펼침/접힘, 파일 클릭은 뷰어로 연다.
function TreeView({
  nodes,
  sourceId,
  filesByPath,
  selectedPaths,
  onToggleFile,
  depth = 0,
}: {
  nodes: TreeNode[];
  sourceId: string;
  filesByPath: Map<string, IndexFile>;
  selectedPaths: Set<string>;
  onToggleFile: (path: string) => void;
  depth?: number;
}) {
  return (
    <ul>
      {nodes.map((node) => (
        <TreeItem
          key={node.path}
          node={node}
          sourceId={sourceId}
          filesByPath={filesByPath}
          selectedPaths={selectedPaths}
          onToggleFile={onToggleFile}
          depth={depth}
        />
      ))}
    </ul>
  );
}

function TreeItem({
  node,
  sourceId,
  filesByPath,
  selectedPaths,
  onToggleFile,
  depth,
}: {
  node: TreeNode;
  sourceId: string;
  filesByPath: Map<string, IndexFile>;
  selectedPaths: Set<string>;
  onToggleFile: (path: string) => void;
  depth: number;
}) {
  const [open, setOpen] = useState(false);
  const openFile = useWorkspace((s) => s.openFile);
  const toggleFilePath = useWorkspace((s) => s.toggleFilePath);
  const focused = useWorkspace(
    (s) => s.viewer?.sourceId === sourceId && s.viewer?.path === node.path,
  );
  const pad = { paddingLeft: `${depth * 11 + 6}px` };

  if (node.type === "dir") {
    // 디렉터리 하위의 supported 파일 경로를 모아 일괄 토글/트라이스테이트 계산.
    const descendant = collectSupportedPaths(node, filesByPath);
    const selectedCount = descendant.filter((p) => selectedPaths.has(p)).length;
    const dirState: "checked" | "unchecked" | "indeterminate" =
      descendant.length === 0
        ? "unchecked"
        : selectedCount === descendant.length
          ? "checked"
          : selectedCount === 0
            ? "unchecked"
            : "indeterminate";

    const toggleDir = () => {
      // 전체 선택돼 있으면 해제, 아니면 전체 선택.
      const selectAll = dirState !== "checked";
      for (const p of descendant) {
        const isSelected = selectedPaths.has(p);
        if (selectAll && !isSelected) toggleFilePath(sourceId, p);
        else if (!selectAll && isSelected) toggleFilePath(sourceId, p);
      }
    };

    return (
      <li>
        <div className="flex items-center" style={pad}>
          {descendant.length > 0 ? (
            <MiniCheckbox
              state={dirState}
              onToggle={toggleDir}
              label={`${node.name} 하위 전체 선택`}
              title="하위 파일 전체 포함/제외"
            />
          ) : (
            <span className="w-5 shrink-0" />
          )}
          <button
            type="button"
            onClick={() => setOpen((o) => !o)}
            className="interactive flex min-w-0 flex-1 items-center gap-1.5 rounded-md py-1 pr-2 text-left text-[12px] hover:bg-secondary"
          >
            <Icon
              name="chevron_right"
              size={12}
              className={cn("shrink-0 text-muted-foreground transition-transform", open && "rotate-90")}
            />
            <Icon name="folder" size={13} className="shrink-0 text-muted-foreground" />
            <span className="truncate">{node.name}</span>
          </button>
        </div>
        {open && node.children ? (
          <TreeView
            nodes={node.children}
            sourceId={sourceId}
            filesByPath={filesByPath}
            selectedPaths={selectedPaths}
            onToggleFile={onToggleFile}
            depth={depth + 1}
          />
        ) : null}
      </li>
    );
  }

  // supported 판정: SSE files[].supported 우선, 없으면 확장자 보조 판정.
  const indexed = filesByPath.get(node.path);
  const supported = indexed ? indexed.supported : isSupportedPath(node.path);
  const status = indexed?.status;
  const selected = selectedPaths.has(node.path);

  return (
    <li>
      <div
        className={cn(
          "flex items-center",
          // 미지원 파일은 반투명으로 비활성처럼 보이게(배지 없음).
          !supported && "opacity-50",
        )}
        style={pad}
      >
        {supported ? (
          <MiniCheckbox
            state={selected ? "checked" : "unchecked"}
            onToggle={() => onToggleFile(node.path)}
            label={`${node.name} 답변 범위 포함`}
            title={selected ? "답변 범위에서 제외" : "답변 범위에 포함"}
          />
        ) : (
          // 미지원 파일은 체크박스를 두지 않고 자리만 맞춘다.
          <span className="w-5 shrink-0" />
        )}
        <button
          type="button"
          onClick={() => openFile(sourceId, node.path)}
          title={supported ? node.path : `${node.path} · 인덱싱 미지원`}
          className={cn(
            "interactive flex min-w-0 flex-1 items-center gap-1.5 rounded-md py-1 pr-2 text-left text-[12px]",
            focused
              ? "bg-accent font-medium text-accent-foreground"
              : "hover:bg-secondary",
            !supported && "cursor-default",
          )}
        >
          <Icon
            name={fileIconForPath(node.path)}
            size={13}
            className={cn(
              "shrink-0",
              focused
                ? "text-accent-foreground"
                : supported
                  ? "text-muted-foreground"
                  : "text-muted-foreground/60",
            )}
          />
          <span className="truncate">{node.name}</span>
          {supported && status ? <FileStatusBadge status={status} /> : null}
        </button>
      </div>
    </li>
  );
}

// 트리 노드(디렉터리 포함) 하위의 supported 파일 경로를 평탄화한다.
function collectSupportedPaths(node: TreeNode, filesByPath: Map<string, IndexFile>): string[] {
  if (node.type === "file") {
    const indexed = filesByPath.get(node.path);
    const supported = indexed ? indexed.supported : isSupportedPath(node.path);
    return supported ? [node.path] : [];
  }
  const out: string[] = [];
  for (const child of node.children ?? []) out.push(...collectSupportedPaths(child, filesByPath));
  return out;
}

function FileStatusBadge({ status }: { status: IndexFile["status"] }) {
  const { icon, spin, className } = fileStatusIcon(status);
  return (
    <Icon
      name={icon}
      size={12}
      className={cn("ml-auto shrink-0", className, spin && "animate-spin")}
    />
  );
}

// 제목 바로 아래 얇은 인라인 진행바(macOS 파일 복사 느낌).
// queued/running일 때만 차오르고, done이면 부드럽게 사라진다. failed면 빨간 톤.
function InlineIndexBar({ progress }: { progress: IndexProgress }) {
  const failed = progress.status === "failed";
  const active = isIndexActive(progress.status);
  // 표시 여부: 진행 중이거나 실패면 보이고, 완료면 높이 0으로 접혀 사라진다.
  const visible = active || failed;
  const clamped = Math.min(100, Math.max(0, progress.percent));

  return (
    <div
      aria-hidden={!visible}
      className={cn(
        "overflow-hidden transition-all duration-500 ease-out",
        visible ? "mt-1 h-[2px] opacity-100" : "mt-0 h-0 opacity-0",
      )}
    >
      <div className="h-[2px] w-full overflow-hidden rounded-full bg-secondary">
        <div
          className={cn(
            "h-full rounded-full transition-[width] duration-300 ease-out",
            failed ? "bg-destructive/85" : "bg-primary",
          )}
          style={{ width: `${failed ? 100 : clamped}%` }}
        />
      </div>
    </div>
  );
}

// 한 행: 본문(뷰어 열기) + 삭제 + 답변 범위 체크박스(repo는 트라이스테이트).
// repo는 펼쳐 파일 트리 + 파일별 체크박스 표시. 마운트되는 동안 인덱싱을 SSE로 구독.
export function SourceRow({ source, notebookId }: { source: Source; notebookId: string }) {
  // 재분석 시 진행 구독을 다시 열기 위한 nonce(변경 시 useIndexProgress 재구독).
  const [resubscribeNonce, setResubscribeNonce] = useState(0);
  // 진행 구독(언마운트/완료 시 내부에서 EventSource close). nonce 변경 시 재구독.
  useIndexProgress(notebookId, source.id, resubscribeNonce);

  const focused = useWorkspace((s) => s.viewer?.sourceId === source.id && !s.viewer?.path);
  const openSource = useWorkspace((s) => s.openSource);
  const removeSource = useWorkspace((s) => s.removeSource);
  const selected = useWorkspace((s) => s.selectedSourceIds.has(source.id));
  const toggleSelected = useWorkspace((s) => s.toggleSourceSelected);
  const progress = useWorkspace((s) => s.indexProgress[source.id]);
  const selectedPaths = useWorkspace((s) => s.selectedFilePaths[source.id]);
  const initFilePaths = useWorkspace((s) => s.initFilePaths);
  const setAllFilePaths = useWorkspace((s) => s.setAllFilePaths);
  const toggleFilePath = useWorkspace((s) => s.toggleFilePath);
  const setIndexProgress = useWorkspace((s) => s.setIndexProgress);

  const [expanded, setExpanded] = useState(false);
  const [tree, setTree] = useState<TreeNode[] | null>(null);
  const [treeLoading, setTreeLoading] = useState(false);
  const [treeError, setTreeError] = useState<string | null>(null);
  // 재분석 진행 중(중복 클릭 방지).
  const [reindexing, setReindexing] = useState(false);
  // 정지 의심 판정용 현재시각 틱. 진행 중일 때만 주기적으로 갱신한다.
  const [now, setNow] = useState(() => Date.now());

  const cfg = SOURCE_KINDS[source.kind];
  const isRepo = source.kind === "repo";
  const filesByPath = indexFilesByPath(progress);
  const supported = supportedFilePaths(progress);
  const failed = progress?.status === "failed";
  const indexing = progress ? isIndexActive(progress.status) : false;
  const done = progress?.status === "done";

  // 진행 중일 때만 5초 간격 타이머로 now를 갱신해 정지 의심을 재평가한다.
  // 진행이 끝나면 타이머를 정리(누수 방지).
  useEffect(() => {
    if (!indexing) return;
    const t = setInterval(() => setNow(Date.now()), 5_000);
    return () => clearInterval(t);
  }, [indexing]);

  // 정지 의심: queued/running인데 updated_at이 임계값 이상 갱신되지 않음.
  const stalled = (() => {
    if (!indexing || !progress) return false;
    const last = new Date(progress.updated_at).getTime();
    if (Number.isNaN(last)) return false;
    return now - last >= STALL_THRESHOLD_MS;
  })();

  // 재분석 버튼 노출 조건: 실패했거나 정지 의심일 때(재분석 중이면 숨김).
  const canReindex = !!progress && (failed || stalled) && !reindexing;

  // 마지막 동기화 시각(진행 중이 아닐 때, done이고 값이 있을 때만 표시).
  const lastSynced =
    done && !indexing ? formatLastSynced(progress?.last_synced_at) : null;

  // 재분석: reindex 호출 → 즉시 queued 스냅샷 반영 → useIndexProgress가 SSE 재구독.
  const handleReindex = async () => {
    if (!notebookId || reindexing) return;
    setReindexing(true);
    try {
      const next = await reindexSource(notebookId, source.id);
      setIndexProgress(source.id, next);
      setNow(Date.now()); // 정지 판정 기준 초기화.
      setResubscribeNonce((n) => n + 1); // SSE 재구독 트리거.
    } catch {
      // 재분석 트리거 실패는 조용히 무시(다음 클릭으로 재시도 가능).
    } finally {
      setReindexing(false);
    }
  };

  // SSE로 supported 파일 목록이 도착하면 기본 전체 선택으로 초기화(이미 있으면 무시).
  useEffect(() => {
    if (isRepo && supported.length > 0) initFilePaths(source.id, supported);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isRepo, source.id, supported.length, initFilePaths]);

  // repo 체크박스 트라이스테이트: 선택 파일 수 ↔ supported 파일 수 비교.
  const effectiveSelected = selectedPaths ?? new Set<string>();
  const selectedCount = supported.filter((p) => effectiveSelected.has(p)).length;
  const repoState: "checked" | "unchecked" | "indeterminate" =
    supported.length === 0
      ? selected
        ? "checked"
        : "unchecked"
      : selectedCount === supported.length
        ? "checked"
        : selectedCount === 0
          ? "unchecked"
          : "indeterminate";

  // repo 행 클릭: 전체 선택/해제 토글(+ 소스 선택 상태 동기화).
  const toggleRepoSelection = () => {
    const next = repoState !== "checked"; // 전체 선택돼 있지 않으면 전체 선택
    if (supported.length > 0) setAllFilePaths(source.id, supported, next);
    // 소스 자체 선택도 맞춘다(전체 선택→포함, 전체 해제→제외).
    if (next && !selected) toggleSelected(source.id);
    else if (!next && selected) toggleSelected(source.id);
  };

  const toggleExpand = async () => {
    const next = !expanded;
    setExpanded(next);
    // 처음 펼칠 때 트리 로드.
    if (next && tree === null && !treeLoading) {
      setTreeLoading(true);
      setTreeError(null);
      try {
        const res = await getTree(notebookId, source.id);
        setTree(res.tree);
      } catch (e) {
        setTreeError(e instanceof Error ? e.message : "트리 로드 실패");
      } finally {
        setTreeLoading(false);
      }
    }
  };

  const handleDelete = async () => {
    try {
      await deleteSource(notebookId, source.id);
      removeSource(source.id);
    } catch {
      // 삭제 실패는 무시(낙관적 미적용). 필요 시 토스트로 확장.
    }
  };

  // 인덱싱 요약 툴팁(완료 후 영구 블록 대신 hover로만 노출).
  const rowTitle = progress
    ? failed
      ? `인덱싱 실패${progress.error ? ` · ${progress.error}` : ""}`
      : indexing
        ? `인덱싱 중 ${progress.processed_files}/${progress.total_files}`
        : `청크 ${progress.indexed_chunks}개 인덱싱 · 미지원 ${progress.skipped_files}개 제외`
    : undefined;

  return (
    <div>
      {/* 한 줄: 체크박스 · kind 아이콘 · 제목(truncate, 하단 인라인 진행바) · (repo) chevron · hover 삭제 */}
      <div
        className={cn(
          "group interactive flex items-center gap-1 rounded-lg pl-1.5 pr-1",
          focused ? "bg-accent" : "hover:bg-secondary",
          // 인덱싱 중에는 살짝 dim(처리 중 느낌). 완료/실패면 또렷하게.
          !selected && !indexing && "opacity-65",
          indexing && "opacity-80",
        )}
      >
        <label
          className="interactive grid h-7 w-7 shrink-0 place-items-center rounded-md text-muted-foreground hover:bg-card/70"
          title={
            isRepo
              ? repoState === "checked"
                ? "파일 전체 범위 해제"
                : "파일 전체 범위 선택"
              : selected
                ? "소스 범위에서 제외"
                : "소스 범위에 포함"
          }
          onClick={(e) => e.stopPropagation()}
        >
          <input
            type="checkbox"
            checked={isRepo ? repoState === "checked" : selected}
            ref={(el) => {
              if (el) el.indeterminate = isRepo && repoState === "indeterminate";
            }}
            onChange={() => (isRepo ? toggleRepoSelection() : toggleSelected(source.id))}
            aria-label={`${source.title} 선택`}
            className="peer sr-only"
          />
          <span
            aria-hidden
            className={cn(
              "grid h-4 w-4 place-items-center rounded-[4px] border border-input bg-card",
              (isRepo ? repoState === "checked" : selected) &&
                "border-primary bg-primary text-primary-foreground",
              isRepo && repoState === "indeterminate" && "border-primary bg-card",
            )}
          >
            {(isRepo ? repoState === "checked" : selected) ? (
              <Icon name="check" size={12} strokeWidth={2.5} />
            ) : isRepo && repoState === "indeterminate" ? (
              <span className="h-2 w-2 rounded-[2px] bg-primary" />
            ) : null}
          </span>
        </label>
        <button
          type="button"
          onClick={() => (isRepo ? toggleExpand() : openSource(source.id))}
          aria-current={focused ? "true" : undefined}
          title={rowTitle ?? (isRepo ? `${cfg.label} · ${source.title} 파일 트리` : `${cfg.label} · ${source.title}`)}
          className="flex min-w-0 flex-1 items-center gap-2 rounded-lg py-1.5 pr-1 text-left"
        >
          <span
            className="grid h-6 w-6 shrink-0 place-items-center rounded-md"
            style={{ background: cfg.chipBg, color: cfg.chipFg }}
          >
            {/* URL 소스는 favicon, 그 외는 정적 아이콘(SourceIcon이 폴백까지 처리). */}
            <SourceIcon
              iconName={cfg.icon}
              url={source.url}
              isUrl={source.kind === "url"}
              size={14}
            />
          </span>
          <span className="min-w-0 flex-1">
            <span
              className={cn(
                "block truncate text-[12px] font-medium leading-tight",
                focused && "text-accent-foreground",
              )}
            >
              {source.title}
              {isRepo && source.branch ? (
                <span
                  className={cn(
                    "ml-1 font-normal",
                    focused ? "text-accent-foreground/60" : "text-muted-foreground/60",
                  )}
                >
                  {source.branch}
                </span>
              ) : null}
            </span>
            {/* 제목 바로 아래 얇은 인라인 진행바 */}
            {progress ? <InlineIndexBar progress={progress} /> : null}
            {/* 실패 시 짧은 에러 한 줄(인라인). */}
            {failed && progress?.error ? (
              <span className="mt-0.5 block truncate text-[10px] text-destructive">
                {progress.error}
              </span>
            ) : null}
            {/* 정지 의심 안내(진행 중인데 일정 시간 갱신 없음). */}
            {stalled && !failed ? (
              <span className="mt-0.5 block truncate text-[10px] text-amber-600 dark:text-amber-500">
                응답이 없어요. 재분석할 수 있습니다.
              </span>
            ) : null}
            {/* 완료된 소스의 마지막 동기화 시각(진행 중이 아닐 때만). */}
            {lastSynced ? (
              <span
                className={cn(
                  "mt-0.5 block truncate text-[10px]",
                  focused ? "text-accent-foreground/60" : "text-muted-foreground/60",
                )}
              >
                마지막 동기화: {lastSynced}
              </span>
            ) : null}
          </span>
          {isRepo ? (
            <Icon
              name="chevron_right"
              size={15}
              className={cn(
                "shrink-0 transition-transform",
                focused ? "text-accent-foreground" : "text-muted-foreground",
                expanded && "rotate-90",
              )}
            />
          ) : null}
        </button>

        {/* 재분석: 실패/정지 의심이거나 재분석 진행 중일 때 노출. 행동 유도라 항상 보이게. */}
        {canReindex || reindexing ? (
          <button
            type="button"
            onClick={handleReindex}
            disabled={reindexing}
            aria-label={`${source.title} 재분석`}
            title={reindexing ? "재분석 중…" : "재분석"}
            className={cn(
              "interactive grid h-7 w-7 shrink-0 place-items-center rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground disabled:cursor-not-allowed",
              failed ? "text-destructive hover:bg-destructive/10" : "",
            )}
          >
            <Icon
              name={reindexing ? "progress_activity" : "refresh"}
              size={14}
              className={reindexing ? "animate-spin" : ""}
            />
          </button>
        ) : null}

        <button
          type="button"
          onClick={handleDelete}
          aria-label={`${source.title} 삭제`}
          title="소스 삭제"
          className="interactive grid h-7 w-7 shrink-0 place-items-center rounded-md text-muted-foreground opacity-0 hover:bg-destructive/10 hover:text-destructive focus-visible:opacity-100 group-hover:opacity-100"
        >
          <Icon name="delete" size={14} />
        </button>
      </div>

      {/* repo 파일 트리(펼쳤을 때). 비repo 소스는 별도 블록을 두지 않는다. */}
      {isRepo && expanded ? (
        <div className="ml-[15px] mt-0.5 border-l border-border pl-1.5">
          {treeLoading ? (
            <p className="flex items-center gap-1.5 px-2 py-1 text-[11px] text-muted-foreground">
              <Icon name="progress_activity" size={12} className="animate-spin" />
              불러오는 중…
            </p>
          ) : treeError ? (
            <p className="px-2 py-1 text-[11px] text-destructive">{treeError}</p>
          ) : tree && tree.length > 0 ? (
            <TreeView
              nodes={tree}
              sourceId={source.id}
              filesByPath={filesByPath}
              selectedPaths={effectiveSelected}
              onToggleFile={(path) => toggleFilePath(source.id, path)}
            />
          ) : (
            <p className="px-2 py-1 text-[11px] text-muted-foreground">파일이 없습니다</p>
          )}
        </div>
      ) : null}
    </div>
  );
}
