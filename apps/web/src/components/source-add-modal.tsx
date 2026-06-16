"use client";

import { useEffect, useState, type ReactNode } from "react";

import {
  createSource,
  getRepoRagSyncJob,
  runRepoRagSync,
  type RepoRagSyncEvent,
  type RepoRagSyncJobView,
  type RepoRagSyncResponse,
} from "../lib/api";
import { cn } from "../lib/cn";
import { useWorkspace } from "../lib/store";
import type { Source, SourceCreate, SourceSyncProgress } from "../lib/types";
import { Icon } from "./icon";
import { Modal } from "./ui/modal";

type Tab = "url" | "repo";

type RepoSyncStatus = "queued" | "running" | "succeeded" | "failed";

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: "url", label: "URL", icon: "link" },
  { id: "repo", label: "GitHub 레포", icon: "github" },
];

const STAGE_ORDER = [
  "job_queued",
  "job_started",
  "job_claimed",
  "lock_acquired",
  "fetch_started",
  "fetch_completed",
  "diff_completed",
  "files_persisted",
  "chunks_upserted",
  "job_succeeded",
  "job_failed",
];

const STAGE_LABELS: Record<string, { label: string; percent: number }> = {
  job_queued: { label: "동기화 큐 등록", percent: 10 },
  job_started: { label: "동기화 시작", percent: 20 },
  job_claimed: { label: "동기화 작업 할당", percent: 30 },
  lock_acquired: { label: "레포 락 획득", percent: 32 },
  fetch_started: { label: "저장소 스냅샷 생성", percent: 45 },
  fetch_completed: { label: "변경점 계산", percent: 60 },
  diff_completed: { label: "변경 내역 분석", percent: 72 },
  files_persisted: { label: "파일 메타 동기화", percent: 84 },
  chunks_upserted: { label: "RAG 인덱스 반영", percent: 92 },
  job_succeeded: { label: "RAG 등록 완료", percent: 100 },
  job_failed: { label: "동기화 실패", percent: 100 },
};

const JOB_STATUS_TO_STAGE: Record<RepoSyncStatus, string> = {
  queued: "job_queued",
  running: "job_started",
  succeeded: "job_succeeded",
  failed: "job_failed",
};

// URL · 레포 추가 모달.
export function SourceAddModal({
  open,
  onClose,
  notebookId,
  initialTab = "url",
}: {
  open: boolean;
  onClose: () => void;
  notebookId: string;
  initialTab?: Tab;
}) {
  const [tab, setTab] = useState<Tab>(initialTab);
  const addSource = useWorkspace((s) => s.addSource);

  useEffect(() => {
    if (open) setTab(initialTab);
  }, [open, initialTab]);

  const submitSource = async (body: SourceCreate): Promise<Source> => {
    const source = await createSource(notebookId, body);
    addSource(source);
    return source;
  };

  return (
    <Modal open={open} onClose={onClose} title="URL · 레포 추가">
      <p className="mb-3 text-[12.5px] leading-relaxed text-muted-foreground">
        파일(PDF · Markdown · 텍스트)은 패널에 끌어다 놓거나 “소스 추가”로 선택하세요. 여기서는
        링크와 GitHub 레포를 등록합니다.
      </p>
      <div
        role="tablist"
        aria-label="소스 추가 방식"
        className="mb-4 flex gap-1 rounded-full bg-secondary p-1"
      >
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              "interactive flex flex-1 items-center justify-center gap-1.5 rounded-full px-2 py-1.5 text-[12px]",
              tab === t.id
                ? "bg-card font-semibold text-foreground shadow-elev-1"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            <Icon name={t.icon} size={15} />
            <span>{t.label}</span>
          </button>
        ))}
      </div>

      {tab === "url" ? (
        <UrlTab onSubmit={submitSource} onDone={onClose} />
      ) : (
        <RepoTab onSubmit={submitSource} onClose={onClose} />
      )}
    </Modal>
  );
}

function useSubmit(onSubmit: (body: SourceCreate) => Promise<Source>, onDone?: () => void) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (build: () => Promise<SourceCreate> | SourceCreate) => {
    setBusy(true);
    setError(null);
    try {
      const body = await build();
      await onSubmit(body);
      onDone?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "추가 실패");
    } finally {
      setBusy(false);
    }
  };

  return { busy, error, run };
}

function inferRepoTitle(url: string) {
  const m = url.match(/github\.com\/(?:[^/]+\/)?([^/]+\/.+?)(?:\.git)?\/?$/);
  return m ? m[1] : url;
}

function deriveRepoProgress(
  job: RepoRagSyncJobView,
  events: RepoRagSyncEvent[],
): {
  stageLabel: string;
  detail: string;
  percent: number;
} {
  const latest = events.at(-1);

  if (latest) {
    const stage = STAGE_LABELS[latest.stage];
    if (stage) {
      return {
        stageLabel: stage.label,
        detail: latest.detail || `${latest.stage}`,
        percent: stage.percent,
      };
    }
  }

  const known = STAGE_LABELS[JOB_STATUS_TO_STAGE[job.status as RepoSyncStatus]];
  if (known) {
    return {
      stageLabel: known.label,
      detail: `상태: ${job.status}`,
      percent: job.status === "succeeded" ? 100 : known.percent,
    };
  }

  return {
    stageLabel: "동기화 진행 중",
    detail: `상태: ${job.status}`,
    percent: 20,
  };
}

function normalizeStatus(payload: RepoRagSyncResponse): RepoSyncStatus {
  if (payload.job.status === "succeeded") return "succeeded";
  if (payload.job.status === "failed") return "failed";
  return "running";
}

async function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function syncRepoAfterCreate(
  source: Source,
  repositoryUrl: string,
  branch: string,
  setSourceSyncStatus: (sourceId: string, status: SourceSyncProgress | null) => void,
): Promise<{ finalStatus: RepoSyncStatus; response: RepoRagSyncResponse }> {
  const start = await runRepoRagSync({
    repository: source.title,
    branch,
    repository_url: repositoryUrl,
  });

  let response = start.response;
  let normalized = normalizeStatus(response);
  let latest = deriveRepoProgress(response.job, response.events);

  setSourceSyncStatus(source.id, {
    sourceId: source.id,
    jobId: response.job.id,
    status: start.status === 200 ? normalized : "running",
    stageLabel: latest.stageLabel,
    detail: latest.detail,
    percent: latest.percent,
  });

  if (start.status === 200 || normalized !== "running") {
    const finalStatus = normalizeStatus(response);
    latest = deriveRepoProgress(response.job, response.events);

    setSourceSyncStatus(source.id, {
      sourceId: source.id,
      jobId: response.job.id,
      status: finalStatus,
      stageLabel: finalStatus === "failed" ? "동기화 실패" : "RAG 등록 완료",
      detail:
        finalStatus === "failed"
          ? response.job.error || latest.detail
          : "레포가 SQL RAG에 저장되어 답변에 반영됩니다.",
      percent: finalStatus === "succeeded" ? 100 : 100,
    });

    return { finalStatus, response };
  }

  for (let attempt = 0; attempt < 180; attempt += 1) {
    await wait(900);
    response = await getRepoRagSyncJob(response.job.id);
    normalized = normalizeStatus(response);
    latest = deriveRepoProgress(response.job, response.events);

    setSourceSyncStatus(source.id, {
      sourceId: source.id,
      jobId: response.job.id,
      status: normalized,
      stageLabel: latest.stageLabel,
      detail: latest.detail,
      percent: latest.percent,
    });

    if (normalized !== "running") {
      break;
    }
  }

  normalized = normalizeStatus(response);
  latest = deriveRepoProgress(response.job, response.events);

  setSourceSyncStatus(source.id, {
    sourceId: source.id,
    jobId: response.job.id,
    status: normalized,
    stageLabel: normalized === "failed" ? "동기화 실패" : latest.stageLabel,
    detail: normalized === "failed" ? response.job.error || latest.detail : latest.detail,
    percent: normalized === "succeeded" ? 100 : latest.percent,
  });

  return { finalStatus: normalized, response };
}

// URL 입력: kind="url".
function UrlTab({ onSubmit, onDone }: { onSubmit: (body: SourceCreate) => Promise<Source>; onDone?: () => void }) {
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const { busy, error, run } = useSubmit(onSubmit, onDone);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        run(() => ({ kind: "url", title: title.trim() || url.trim(), url: url.trim() }));
      }}
      className="space-y-3"
    >
      <Field label="URL">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/docs"
          className={inputCls}
        />
      </Field>
      <Field label="제목 (선택)">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="비우면 URL을 제목으로 사용"
          className={inputCls}
        />
      </Field>
      {error ? <ErrorText>{error}</ErrorText> : null}
      <SubmitButton disabled={!url.trim() || busy}>{busy ? "추가 중…" : "URL 추가"}</SubmitButton>
    </form>
  );
}

// GitHub 레포 등록: repository_url + branch, kind="repo".
function RepoTab({ onSubmit, onClose }: { onSubmit: (body: SourceCreate) => Promise<Source>; onClose: () => void }) {
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progressLabel, setProgressLabel] = useState("");
  const [progressPercent, setProgressPercent] = useState(0);
  const [syncing, setSyncing] = useState(false);

  const setSourceSyncStatus = useWorkspace((s) => s.setSourceSyncStatus);

  const run = async () => {
    if (busy) return;
    if (!repoUrl.trim()) return;

    const normalizedRepoUrl = repoUrl.trim();
    const normalizedBranch = branch.trim() || "main";
    const sourceTitle = inferRepoTitle(normalizedRepoUrl);

    setBusy(true);
    setSyncing(false);
    setError(null);
    setProgressLabel("레포 등록을 시작합니다");
    setProgressPercent(6);

    try {
      const source = await onSubmit({
        kind: "repo",
        title: sourceTitle,
        repository_url: normalizedRepoUrl,
        branch: normalizedBranch,
      });

      setSourceSyncStatus(source.id, {
        sourceId: source.id,
        jobId: "init",
        status: "queued",
        stageLabel: "레포 등록 완료",
        detail: "레포 스냅샷 생성 및 SQL RAG 동기화를 시작합니다.",
        percent: 6,
      });

      setSyncing(true);
      setProgressLabel("레포 동기화를 실행합니다");
      const result = await syncRepoAfterCreate(source, normalizedRepoUrl, normalizedBranch, setSourceSyncStatus);
      const finalProgress = deriveRepoProgress(result.response.job, result.response.events);
      const finalStatus = result.finalStatus;

      setProgressLabel(
        finalStatus === "succeeded" ? "RAG 인덱싱이 완료되었습니다" : finalProgress.stageLabel,
      );
      setProgressPercent(
        finalStatus === "succeeded"
          ? 100
          : Math.min(100, Math.max(progressPercent, finalProgress.percent, 96)),
      );

      if (finalStatus === "succeeded") {
        setProgressLabel("레포가 SQL RAG에 등록되었습니다");
        setProgressPercent(100);
        onClose();
      }

      if (finalStatus === "failed") {
        throw new Error(result.response.job.error || finalProgress.detail || "레포 동기화에 실패했습니다");
      }
    } catch (e) {
      const message = e instanceof Error ? e.message : "레포 등록 실패";
      setError(message);
      setProgressLabel("레포 등록 실패");
      setProgressPercent(100);
    } finally {
      setBusy(false);
      setSyncing(false);
    }
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        void run();
      }}
      className="space-y-3"
    >
      <Field label="레포 URL">
        <input
          type="url"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          placeholder="https://github.com/org/repo"
          className={inputCls}
        />
      </Field>
      <Field label="브랜치">
        <input
          value={branch}
          onChange={(e) => setBranch(e.target.value)}
          placeholder="main"
          className={inputCls}
        />
      </Field>
      <p className="text-[12px] text-muted-foreground">
        등록하면 해당 브랜치를 인덱싱합니다. 가시성은 GitHub 접근 권한을 따릅니다.
      </p>
      {error ? <ErrorText>{error}</ErrorText> : null}
      <SubmitButton disabled={!repoUrl.trim() || busy}>
        {busy ? "레포 등록 중…" : "레포 등록"}
      </SubmitButton>

      {syncing || progressPercent > 0 ? (
        <div className="rounded-xl border border-border bg-card p-2.5 text-[12px] text-muted-foreground">
          <div className="mb-2 flex items-center justify-between">
            <span className="flex items-center gap-1.5 font-semibold text-foreground">
              <Icon
                name={busy ? "progress_activity" : "check_circle"}
                size={14}
                className={busy ? "animate-spin" : undefined}
              />
              <span>레포 인덱싱 진행</span>
            </span>
            <span>{Math.min(100, progressPercent)}%</span>
          </div>
          <div className="mb-1.5 h-1.5 w-full rounded-full bg-secondary">
            <div
              className="h-full rounded-full bg-primary/85 transition-all duration-300"
              style={{ width: `${Math.min(100, progressPercent)}%` }}
            />
          </div>
          <p>{progressLabel || "처리 대기 중"}</p>
        </div>
      ) : null}
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

function ErrorText({ children }: { children: React.ReactNode }) {
  return <p className="text-[12px] text-destructive">{children}</p>;
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
