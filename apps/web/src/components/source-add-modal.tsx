"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

import {
  createSource,
  fetchGitHubRepoInfo,
  getLinkMetadata,
  parseGitHubRepo,
  type GitHubRepoInfo,
} from "../lib/api";
import { cn } from "../lib/cn";
import { useWorkspace } from "../lib/store";
import type { LinkMetadata, Source, SourceCreate } from "../lib/types";
import { Collapse } from "./ui/collapse";
import { Icon } from "./icon";
import { SourceIcon } from "./source-icon";
import { Button } from "./ui/button";
import { Modal } from "./ui/modal";

// 통합 소스 추가 모달.
// 한 모달 안에서 (a) 파일 드롭존(드래그앤드롭 + 클릭 선택) + (b) URL/GitHub 입력을 모두 처리한다.
// 입력 URL이 github.com/{owner}/{repo} 형태이면 디바운스로 GitHub 공개 API를 조회해
// 브랜치 목록을 인식하고, 인식되면 커스텀 브랜치 드롭다운이 입력란 "아래로" 펼쳐진다.
// 제출 시 GitHub면 kind="repo"(repository_url+branch), 아니면 kind="url".
export function SourceAddModal({
  open,
  onClose,
  notebookId,
  processFiles,
  busy,
}: {
  open: boolean;
  onClose: () => void;
  notebookId: string;
  // 파일 일괄 처리(소스 추가 흐름의 단일 소유자에서 주입).
  processFiles: (files: FileList | File[]) => Promise<void>;
  busy: boolean;
}) {
  const addSource = useWorkspace((s) => s.addSource);

  const submitSource = async (body: SourceCreate): Promise<Source> => {
    const source = await createSource(notebookId, body);
    addSource(source);
    return source;
  };

  return (
    <Modal open={open} onClose={onClose} title="소스 추가">
      {open ? (
        <div className="space-y-4">
          {/* (a) 파일 드롭존 */}
          <FileDropzone
            processFiles={processFiles}
            busy={busy}
            onDone={onClose}
          />

          {/* 구분선 */}
          <div className="flex items-center gap-3 text-[11px] font-medium text-muted-foreground">
            <span className="h-px flex-1 bg-border" />
            또는 링크로 추가
            <span className="h-px flex-1 bg-border" />
          </div>

          {/* (b) URL/GitHub 입력 */}
          <LinkForm onSubmit={submitSource} onClose={onClose} />
        </div>
      ) : null}
    </Modal>
  );
}

// 파일 드롭존: 드래그앤드롭 + 클릭하여 선택. 처리 성공 시 모달을 닫는다.
function FileDropzone({
  processFiles,
  busy,
  onDone,
}: {
  processFiles: (files: FileList | File[]) => Promise<void>;
  busy: boolean;
  onDone: () => void;
}) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const dragDepth = useRef(0);
  const [dragActive, setDragActive] = useState(false);

  // 파일을 처리하고 끝나면 모달을 닫는다.
  const handle = async (files: FileList | File[]) => {
    if (!files || (files as FileList).length === 0) return;
    await processFiles(files);
    onDone();
  };

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
    if (e.dataTransfer.files?.length) await handle(e.dataTransfer.files);
  };

  return (
    <div>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragEnter={onDragEnter}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={cn(
          "transition-all duration-200 ease-in-out flex w-full flex-col items-center gap-2 rounded-2xl border-2 border-dashed px-4 py-6 text-center",
          dragActive
            ? "border-primary bg-accent/70 text-accent-foreground"
            : "border-border bg-secondary/40 text-muted-foreground hover:border-primary/40 hover:bg-secondary/60 hover:text-foreground",
        )}
      >
        <span className="grid h-10 w-10 place-items-center rounded-2xl bg-primary text-primary-foreground">
          <Icon name={busy ? "progress_activity" : "upload_file"} size={20} className={busy ? "animate-spin" : ""} />
        </span>
        <span className="text-[12px] font-semibold text-foreground">
          {busy ? "파일 처리 중…" : "파일을 끌어다 놓거나 클릭하여 선택"}
        </span>
        <span className="text-[11px]">PDF · Markdown · 텍스트</span>
      </button>
      {/* 시각적으로 숨긴 파일 input(클릭/드롭존 공용) */}
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".pdf,.md,.markdown,.txt,text/plain,text/markdown,application/pdf"
        className="hidden"
        onChange={async (e) => {
          if (e.target.files) await handle(e.target.files);
          e.target.value = ""; // 같은 파일 재선택 허용
        }}
      />
    </div>
  );
}

// GitHub면 owner/repo, 일반 URL이면 호스트+마지막 경로 세그먼트로 제목을 자동 도출.
// 주의: 실제 HTML <title>은 CORS로 브라우저에서 직접 fetch할 수 없으므로 URL 기반으로만 채운다.
function inferTitleFromUrl(raw: string): string {
  const url = raw.trim();
  if (!url) return "";
  // GitHub: owner/repo
  const gh = parseGitHubRepo(url);
  if (gh) return `${gh.owner}/${gh.repo}`;
  // 일반 URL: 호스트 + 마지막 경로 세그먼트
  try {
    const u = new URL(url.includes("://") ? url : `https://${url}`);
    const segs = u.pathname.split("/").filter(Boolean);
    const last = segs.length > 0 ? segs[segs.length - 1] : "";
    return last ? `${u.hostname} · ${decodeURIComponent(last)}` : u.hostname;
  } catch {
    return url;
  }
}

// GitHub 인식 상태(머신).
type GhState =
  | { kind: "none" } // GitHub URL 아님 → 일반 URL
  | { kind: "loading" } // 브랜치 인식 중
  | { kind: "ready"; info: GitHubRepoInfo } // 인식 성공
  | { kind: "error"; message: string }; // 비공개·레이트리밋·실패 → 수동 입력 폴백

function LinkForm({
  onSubmit,
  onClose,
}: {
  onSubmit: (body: SourceCreate) => Promise<Source>;
  onClose: () => void;
}) {
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  // 사용자가 제목을 직접 수정했는지(수정했다면 자동 채움을 멈춘다).
  const [titleEdited, setTitleEdited] = useState(false);
  const [branch, setBranch] = useState(""); // 선택/수동 입력 브랜치
  const [gh, setGh] = useState<GhState>({ kind: "none" });
  // 비-GitHub URL의 링크 메타데이터(실제 제목/아이콘). 로딩/결과 표시용.
  const [meta, setMeta] = useState<LinkMetadata | null>(null);
  const [metaLoading, setMetaLoading] = useState(false);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 디바운스/취소 관리(GitHub 브랜치 인식).
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  // 디바운스/취소 관리(링크 메타데이터).
  const metaDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const metaAbortRef = useRef<AbortController | null>(null);

  // URL 변경 → 제목 자동 채움(사용자가 직접 수정 전까지) + github 형태이면 브랜치 인식.
  useEffect(() => {
    // 제목 임시 자동 채움: URL 기반(즉시 피드백). 비-GitHub URL은 아래 메타 효과가
    // 실제 HTML 제목으로 덮어쓴다(사용자가 직접 수정하지 않은 경우에 한함).
    if (!titleEdited) setTitle(inferTitleFromUrl(url));

    if (debounceRef.current) clearTimeout(debounceRef.current);
    abortRef.current?.abort();

    const parsed = parseGitHubRepo(url);
    if (!parsed) {
      setGh({ kind: "none" });
      return;
    }

    setGh({ kind: "loading" });
    const controller = new AbortController();
    abortRef.current = controller;
    debounceRef.current = setTimeout(async () => {
      try {
        const info = await fetchGitHubRepoInfo(parsed.owner, parsed.repo, controller.signal);
        setGh({ kind: "ready", info });
        // 기본 브랜치를 미리 선택(사용자가 아직 손대지 않았으면).
        setBranch((prev) => prev || info.defaultBranch);
      } catch (e) {
        if (controller.signal.aborted) return; // 입력이 더 들어와 취소된 경우는 무시.
        setGh({
          kind: "error",
          message:
            e instanceof Error
              ? `브랜치 자동 인식 실패(${e.message}). 비공개이거나 한도 초과일 수 있어요. 브랜치를 직접 입력하세요.`
              : "브랜치 자동 인식 실패. 브랜치를 직접 입력하세요.",
        });
      }
    }, 450);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      controller.abort();
    };
  }, [url, titleEdited]);

  // 비-GitHub URL → 디바운스로 링크 메타데이터 조회(실제 HTML 제목/아이콘).
  // 성공하고 사용자가 제목을 직접 수정하지 않았으면 실제 제목으로 덮어쓴다.
  useEffect(() => {
    if (metaDebounceRef.current) clearTimeout(metaDebounceRef.current);
    metaAbortRef.current?.abort();

    const trimmed = url.trim();
    const parsed = parseGitHubRepo(trimmed);
    // GitHub는 브랜치 인식 경로가 처리하므로 메타 조회 대상이 아니다.
    if (!trimmed || parsed) {
      setMeta(null);
      setMetaLoading(false);
      return;
    }
    // 그럴듯한 URL 형태일 때만 조회(점이 있거나 스킴 포함).
    if (!trimmed.includes(".") && !trimmed.includes("://")) {
      setMeta(null);
      setMetaLoading(false);
      return;
    }

    setMetaLoading(true);
    const controller = new AbortController();
    metaAbortRef.current = controller;
    metaDebounceRef.current = setTimeout(async () => {
      try {
        const data = await getLinkMetadata(trimmed, controller.signal);
        if (controller.signal.aborted) return;
        setMeta(data);
        // 사용자가 직접 수정하지 않았고 실제 제목이 있으면 자동 채움.
        if (data.title) {
          setTitle((prev) => (titleEdited ? prev : data.title ?? prev));
        }
      } catch {
        if (controller.signal.aborted) return;
        // 메타 조회 실패는 조용히 무시(URL 기반 제목으로 폴백).
        setMeta(null);
      } finally {
        if (!controller.signal.aborted) setMetaLoading(false);
      }
    }, 500);

    return () => {
      if (metaDebounceRef.current) clearTimeout(metaDebounceRef.current);
      controller.abort();
    };
  }, [url, titleEdited]);

  const isGitHub = gh.kind !== "none";
  // 브랜치 영역(드롭다운 또는 수동 입력)을 펼칠지 여부.
  const branchOpen = isGitHub;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) return;
    setBusy(true);
    setError(null);
    try {
      let body: SourceCreate;
      if (isGitHub) {
        const b = branch.trim() || (gh.kind === "ready" ? gh.info.defaultBranch : "main");
        body = {
          kind: "repo",
          title: title.trim() || inferTitleFromUrl(trimmed),
          repository_url: trimmed,
          branch: b,
        };
      } else {
        // 제목 우선순위: 사용자/메타 제목 → URL 도출 → 원문 URL.
        const urlTitle = title.trim() || meta?.title?.trim() || inferTitleFromUrl(trimmed) || trimmed;
        body = { kind: "url", title: urlTitle, url: trimmed };
      }
      await onSubmit(body);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "추가 실패");
    } finally {
      setBusy(false);
    }
  };

  const submitLabel = busy
    ? isGitHub
      ? "레포 등록 중…"
      : "추가 중…"
    : isGitHub
      ? "레포 등록"
      : "URL 추가";

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {/* 상단 설명: 짧고 한 줄(줄바꿈 방지). */}
      <p className="truncate text-[12px] text-muted-foreground">
        문서·위키 URL이나 GitHub 저장소 주소를 붙여넣으세요.
      </p>

      <Field label="URL">
        <div className="relative">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/docs · https://github.com/org/repo"
            className={inputCls}
          />
          {/* 인식 상태 인디케이터(입력 우측): GitHub 우선, 아니면 링크 메타 로딩/사이트 아이콘. */}
          {gh.kind === "loading" ? (
            <Icon
              name="progress_activity"
              size={15}
              className="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-muted-foreground"
            />
          ) : gh.kind === "ready" ? (
            <Icon
              name="github"
              size={15}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-primary"
            />
          ) : metaLoading ? (
            <Icon
              name="progress_activity"
              size={15}
              className="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-muted-foreground"
            />
          ) : !isGitHub && url.trim() ? (
            // 비-GitHub URL: 사이트 아이콘 미리보기(favicon/icon_url 폴백은 SourceIcon이 처리).
            <span className="absolute right-3 top-1/2 -translate-y-1/2">
              <SourceIcon iconName="link" url={url.trim()} isUrl size={15} />
            </span>
          ) : null}
        </div>
      </Field>

      {/* GitHub로 인식되면 애니메이션으로 늘어나며 브랜치 선택 영역이 입력란 바로 아래에 나타난다. */}
      <Collapse open={branchOpen}>
        <div className="space-y-3 pt-0.5">
          {gh.kind === "ready" ? (
            <Field label="브랜치">
              {/* 커스텀 드롭다운: 입력란 바로 "아래로" 펼쳐진다(네이티브 select 중앙팝업 회피). */}
              <BranchDropdown
                branches={gh.info.branches}
                defaultBranch={gh.info.defaultBranch}
                value={branch || gh.info.defaultBranch}
                onChange={setBranch}
              />
              <p className="text-[11.5px] text-muted-foreground">
                {gh.info.branches.length}개 브랜치를 인식했어요. 선택한 브랜치를 인덱싱합니다.
              </p>
            </Field>
          ) : gh.kind === "error" ? (
            <Field label="브랜치">
              <input
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                placeholder="main"
                className={inputCls}
              />
              <p className="text-[11.5px] text-destructive">{gh.message}</p>
            </Field>
          ) : (
            // loading: 영역만 열어두고 안내.
            <p className="flex items-center gap-1.5 text-[12px] text-muted-foreground">
              <Icon name="progress_activity" size={13} className="animate-spin" />
              GitHub 저장소 브랜치를 인식하는 중…
            </p>
          )}
        </div>
      </Collapse>

      <Field label="제목 (선택)">
        <input
          value={title}
          onChange={(e) => {
            setTitle(e.target.value);
            setTitleEdited(true); // 직접 수정 시 자동 채움 중단.
          }}
          placeholder={isGitHub ? "비우면 레포 이름을 사용" : "비우면 URL을 제목으로 사용"}
          className={inputCls}
        />
        {/* 비-GitHub URL 메타 설명 미리보기(있을 때만, 한 줄). */}
        {!isGitHub && meta?.description ? (
          <p className="truncate text-[11px] text-muted-foreground">{meta.description}</p>
        ) : null}
      </Field>

      {error ? <p className="text-[12px] text-destructive">{error}</p> : null}

      <SubmitButton disabled={!url.trim() || busy || gh.kind === "loading"}>
        {submitLabel}
      </SubmitButton>
    </form>
  );
}

// 커스텀 브랜치 드롭다운. 트리거 클릭 시 옵션 목록이 입력란 바로 아래로 Collapse 애니메이션과
// 함께 펼쳐진다. 바깥 클릭으로 닫힌다(네이티브 select의 화면 중앙 팝업 문제 해결).
function BranchDropdown({
  branches,
  defaultBranch,
  value,
  onChange,
}: {
  branches: string[];
  defaultBranch: string;
  value: string;
  onChange: (b: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDocClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className={cn(inputCls, "flex items-center justify-between text-left")}
      >
        <span className="truncate">
          {value}
          {value === defaultBranch ? " (기본)" : ""}
        </span>
        <Icon
          name="unfold_more"
          size={15}
          className="ml-2 shrink-0 text-muted-foreground"
        />
      </button>
      {/* 입력란 바로 아래에서 height/opacity로 부드럽게 펼침. */}
      <Collapse open={open} className="absolute left-0 right-0 top-full z-20 mt-1">
        <div className="max-h-52 overflow-y-auto rounded-xl border border-border bg-card py-1 shadow">
          {branches.map((b) => (
            <button
              key={b}
              type="button"
              role="option"
              aria-selected={b === value}
              onClick={() => {
                onChange(b);
                setOpen(false);
              }}
              className={cn(
                "transition-all duration-200 ease-in-out flex w-full items-center justify-between gap-2 px-3 py-1.5 text-left text-[12px] hover:bg-secondary",
                b === value ? "font-semibold text-foreground" : "text-muted-foreground",
              )}
            >
              <span className="truncate">
                {b}
                {b === defaultBranch ? " (기본)" : ""}
              </span>
              {b === value ? <Icon name="check" size={14} className="shrink-0 text-primary" /> : null}
            </button>
          ))}
        </div>
      </Collapse>
    </div>
  );
}

// 입력 텍스트는 공용 입력 규격(h-8 px-3 text-[12px])과 일관되게 통일.
// BranchDropdown 트리거도 이 클래스를 공유하므로 flex 정렬은 호출부에서 덧붙인다.
const inputCls =
  "transition-all duration-200 ease-in-out h-8 w-full rounded-lg border border-border bg-background px-3 text-[12px] font-medium outline-none placeholder:font-normal placeholder:text-muted-foreground focus:border-primary/60 focus:ring-2 focus:ring-primary/15";

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block space-y-1.5">
      <span className="text-[12px] font-medium">{label}</span>
      {children}
    </label>
  );
}

function SubmitButton({
  disabled,
  children,
}: {
  disabled: boolean;
  children: React.ReactNode;
}) {
  // 공용 primary 알약(전폭). 모달 제출 일관화.
  return (
    <Button type="submit" variant="primary" size="sm" disabled={disabled} className="w-full">
      {children}
    </Button>
  );
}
