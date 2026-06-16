"use client";

import { useState } from "react";

import { useWorkspace } from "../lib/store";
import { Icon } from "./icon";
import { SourceAddModal } from "./source-add-modal";
import { SourceRow } from "./source-row";
import { Panel } from "./ui/panel";

export function SourcesPanel({ notebookId }: { notebookId: string }) {
  const [addOpen, setAddOpen] = useState(false);
  const sources = useWorkspace((s) => s.sources);

  return (
    <Panel as="aside" className="w-[324px] shrink-0">
      {/* 헤더 */}
      <div className="flex items-center justify-between px-4 pt-4 pb-1">
        <h2 className="text-[15px] font-semibold tracking-tight">소스</h2>
        {sources.length > 0 ? (
          <span className="rounded-full bg-secondary px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
            {sources.length}
          </span>
        ) : null}
      </div>

      {/* 가로 꽉 찬 아웃라인 pill: 소스 추가 */}
      <div className="px-4 pb-2 pt-1">
        <button
          type="button"
          onClick={() => setAddOpen(true)}
          className="interactive flex w-full items-center justify-center gap-2 rounded-full border border-border bg-card px-4 py-2.5 text-[13px] font-medium text-foreground hover:bg-secondary hover:shadow-elev-1 active:scale-[0.99]"
        >
          <Icon name="add" size={18} className="text-primary" />
          소스 추가
        </button>
      </div>

      <div className="scroll-thin flex-1 overflow-y-auto px-2 pb-3 pt-1">
        {sources.length === 0 ? (
          <div className="mt-10 px-4 text-center">
            <span className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-accent text-accent-foreground">
              <Icon name="description" size={26} />
            </span>
            <p className="mt-4 text-[14px] font-semibold">저장된 소스가 없습니다</p>
            <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted-foreground">
              레포·문서·PDF·URL을 추가하면 답변의 근거로 사용됩니다.
            </p>
            <button
              type="button"
              onClick={() => setAddOpen(true)}
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
            <div className="space-y-0.5">
              {sources.map((s) => (
                <SourceRow key={s.id} source={s} notebookId={notebookId} />
              ))}
            </div>
          </>
        )}
      </div>

      <SourceAddModal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        notebookId={notebookId}
      />
    </Panel>
  );
}
