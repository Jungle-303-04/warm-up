"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

import {
  createSource,
  fetchGitHubRepoInfo,
  parseGitHubRepo,
  type GitHubRepoInfo,
} from "../lib/api";
import { cn } from "../lib/cn";
import { useWorkspace } from "../lib/store";
import type { Source, SourceCreate } from "../lib/types";
import { Collapse } from "./ui/collapse";
import { Icon } from "./icon";
import { Modal } from "./ui/modal";

// 링크(URL · GitHub) 통합 추가 모달.
// 입력은 URL 하나. 값이 github.com/{owner}/{repo} 형태이면 디바운스로 GitHub
// 공개 API를 조회해 브랜치 목록을 인식하고, 인식되면 브랜치 드롭다운이 열린다.
// 제출 시 GitHub면 kind="repo"(repository_url+branch), 아니면 kind="url".
export function SourceAddModal({
  open,
  onClose,
  notebookId,
}: {
  open: boolean;
  onClose: () => void;
  notebookId: string;
}) {
  const addSource = useWorkspace((s) => s.addSource);

  const submitSource = async (body: SourceCreate): Promise<Source> => {
    const source = await createSource(notebookId, body);
    addSource(source);
    return source;
  };

  return (
    <Modal open={open} onClose={onClose} title="링크 추가">
      <p className="mb-4 text-[12.5px] leading-relaxed text-muted-foreground">
        문서 페이지·위키 링크나 GitHub 저장소 주소를 붙여넣으세요. GitHub 주소면 브랜치를
        자동으로 인식합니다. 파일(PDF · Markdown · 텍스트)은 패널에 끌어다 놓거나 “소스 추가”로
        선택하세요.
      </p>
      {open ? <LinkForm onSubmit={submitSource} onClose={onClose} /> : null}
    </Modal>
  );
}

function inferRepoTitle(url: string) {
  const m = url.match(/github\.com\/(?:[^/]+\/)?([^/]+\/.+?)(?:\.git)?\/?$/);
  return m ? m[1] : url;
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
  const [branch, setBranch] = useState(""); // 선택/수동 입력 브랜치
  const [gh, setGh] = useState<GhState>({ kind: "none" });

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 디바운스/취소 관리.
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // URL 변경 → github 형태이면 디바운스로 브랜치 인식.
  useEffect(() => {
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
  }, [url]);

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
          title: title.trim() || inferRepoTitle(trimmed),
          repository_url: trimmed,
          branch: b,
        };
      } else {
        body = { kind: "url", title: title.trim() || trimmed, url: trimmed };
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
      <Field label="URL">
        <div className="relative">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/docs · https://github.com/org/repo"
            className={inputCls}
          />
          {/* GitHub 인식 상태 인디케이터(입력 우측). */}
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
          ) : null}
        </div>
      </Field>

      {/* GitHub로 인식되면 애니메이션으로 늘어나며 브랜치 선택 영역이 나타난다. */}
      <Collapse open={branchOpen}>
        <div className="space-y-3 pt-0.5">
          {gh.kind === "ready" ? (
            <Field label="브랜치">
              {/* 인식된 브랜치 리스트박스. 기본=default_branch 미리선택. */}
              <div className="relative">
                <select
                  value={branch || gh.info.defaultBranch}
                  onChange={(e) => setBranch(e.target.value)}
                  className={cn(inputCls, "appearance-none pr-9")}
                  aria-label="브랜치 선택"
                >
                  {gh.info.branches.map((b) => (
                    <option key={b} value={b}>
                      {b}
                      {b === gh.info.defaultBranch ? " (기본)" : ""}
                    </option>
                  ))}
                </select>
                <Icon
                  name="unfold_more"
                  size={15}
                  className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
                />
              </div>
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
          onChange={(e) => setTitle(e.target.value)}
          placeholder={isGitHub ? "비우면 레포 이름을 사용" : "비우면 URL을 제목으로 사용"}
          className={inputCls}
        />
      </Field>

      {isGitHub ? (
        <p className="text-[12px] text-muted-foreground">
          등록하면 해당 브랜치를 백그라운드로 인덱싱합니다. 진행 상황은 소스 목록에서 실시간으로
          확인할 수 있어요.
        </p>
      ) : null}

      {error ? <p className="text-[12px] text-destructive">{error}</p> : null}

      <SubmitButton disabled={!url.trim() || busy || gh.kind === "loading"}>
        {submitLabel}
      </SubmitButton>
    </form>
  );
}

const inputCls =
  "interactive w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-[13px] outline-none placeholder:text-muted-foreground focus:border-primary/60 focus:ring-2 focus:ring-primary/15";

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block space-y-1.5">
      <span className="text-[13px] font-medium">{label}</span>
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
  return (
    <button
      type="submit"
      disabled={disabled}
      className="interactive w-full rounded-full bg-primary py-2.5 text-[13px] font-medium text-primary-foreground hover:opacity-90 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-40 disabled:active:scale-100"
    >
      {children}
    </button>
  );
}
