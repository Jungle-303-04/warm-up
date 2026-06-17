"use client";

import { useEffect } from "react";

import { getIndexProgress, openIndexStream, reindexSource } from "../lib/api";
import { isIndexActive } from "../lib/indexing";
import { useWorkspace } from "../lib/store";
import type { IndexProgress } from "../lib/types";

const POLL_INTERVAL_MS = 5_000;
const STALE_AUTORECOVER_MS = 5 * 60_000;
const AUTORECOVER_COOLDOWN_MS = 5 * 60_000;

function isTerminal(progress: IndexProgress): boolean {
  return progress.status === "done" || progress.status === "failed";
}

function isStaleActiveProgress(progress: IndexProgress, now: number): boolean {
  if (!isIndexActive(progress.status)) return false;
  const updatedAt = new Date(progress.updated_at).getTime();
  if (Number.isNaN(updatedAt)) return false;
  return now - updatedAt >= STALE_AUTORECOVER_MS;
}

// 한 소스의 RAG 인덱싱 진행을 구독한다.
// 1) 마운트 시 서버 스냅샷 복원 → 2) SSE 구독 → 3) 5초 폴링으로 헬스체크.
// SSE가 끊겨도 진행 중인 작업을 실패로 간주하지 않고, 다음 폴링에서 상태를 복구한다.
// 서버 재시작 등으로 running 상태만 DB에 남아 오래 갱신되지 않으면 조용히 재분석을 예약한다.
// resubscribeKey가 바뀌면(재분석 트리거 등) 다시 조회·구독한다.
export function useIndexProgress(
  notebookId: string | null,
  sourceId: string,
  resubscribeKey?: number,
) {
  const setIndexProgress = useWorkspace((s) => s.setIndexProgress);

  useEffect(() => {
    if (!notebookId) return;
    let active = true;
    let stream: { close: () => void } | null = null;
    let pollTimer: ReturnType<typeof setInterval> | null = null;
    let recovering = false;
    let lastRecoverAttemptAt = 0;

    const closeStream = () => {
      stream?.close();
      stream = null;
    };

    const stopPolling = () => {
      if (pollTimer === null) return;
      clearInterval(pollTimer);
      pollTimer = null;
    };

    const applyProgress = (progress: IndexProgress) => {
      if (!active) return;
      setIndexProgress(sourceId, progress);
      if (isTerminal(progress)) {
        closeStream();
        stopPolling();
      }
    };

    const ensureStream = () => {
      if (!active || stream !== null) return;
      stream = openIndexStream(
        notebookId,
        sourceId,
        applyProgress,
        (last) => {
          stream = null;
          if (last) applyProgress(last);
        },
      );
    };

    const recoverIfStale = async (progress: IndexProgress): Promise<boolean> => {
      const now = Date.now();
      if (!isStaleActiveProgress(progress, now)) return false;
      if (recovering || now - lastRecoverAttemptAt < AUTORECOVER_COOLDOWN_MS) return false;

      recovering = true;
      lastRecoverAttemptAt = now;
      closeStream();
      try {
        const next = await reindexSource(notebookId, sourceId);
        if (!active) return true;
        applyProgress(next);
        if (!isTerminal(next)) ensureStream();
        return true;
      } catch {
        // 재분석 예약 실패는 다음 폴링에서 다시 판단한다. 화면에는 raw 에러를 노출하지 않는다.
        return false;
      } finally {
        recovering = false;
      }
    };

    const poll = async () => {
      try {
        const progress = await getIndexProgress(notebookId, sourceId);
        if (!active) return;
        if (await recoverIfStale(progress)) return;
        applyProgress(progress);
        if (!isTerminal(progress)) ensureStream();
      } catch {
        // 추가 직후 레코드 생성 타이밍 차이, SSE 일시 단절, 프록시 지연은 다음 tick에서 복구한다.
        if (!active) return;
        ensureStream();
      }
    };

    void poll();
    pollTimer = setInterval(() => void poll(), POLL_INTERVAL_MS);

    return () => {
      active = false;
      closeStream();
      stopPolling();
    };
  }, [notebookId, sourceId, setIndexProgress, resubscribeKey]);
}
