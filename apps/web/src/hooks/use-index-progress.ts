"use client";

import { useEffect } from "react";

import { getIndexProgress, openIndexStream } from "../lib/api";
import { useWorkspace } from "../lib/store";

// 한 소스의 RAG 인덱싱 진행을 구독한다.
// 1) 마운트 시 1회 조회로 현재 상태 복원 → 2) SSE 구독으로 실시간 갱신.
// status done/failed면 SSE는 스스로 종료하고, 언마운트 시에도 반드시 close(누수 방지).
export function useIndexProgress(notebookId: string | null, sourceId: string) {
  const setIndexProgress = useWorkspace((s) => s.setIndexProgress);

  useEffect(() => {
    if (!notebookId) return;
    let active = true;
    let stream: { close: () => void } | null = null;

    // 1회 조회로 초기 상태 복원(이미 완료된 소스도 한 번에 반영).
    getIndexProgress(notebookId, sourceId)
      .then((progress) => {
        if (!active) return;
        setIndexProgress(sourceId, progress);
        // 이미 끝난 작업은 굳이 SSE를 열지 않는다.
        if (progress.status === "done" || progress.status === "failed") return;
        stream = openIndexStream(notebookId, sourceId, (next) => {
          if (active) setIndexProgress(sourceId, next);
        });
      })
      .catch(() => {
        // 1회 조회 실패해도 SSE는 시도(추가 직후 레코드 생성 타이밍 차이 대비).
        if (!active) return;
        stream = openIndexStream(notebookId, sourceId, (next) => {
          if (active) setIndexProgress(sourceId, next);
        });
      });

    return () => {
      active = false;
      stream?.close();
    };
  }, [notebookId, sourceId, setIndexProgress]);
}
