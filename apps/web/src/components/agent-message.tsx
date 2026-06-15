import type { AgentResponse, Citation } from "../lib/types";
import { CitationChip } from "./citation-chip";
import { Icon } from "./icon";

// 인용을 표시용 라벨로. 경로+줄범위 > 경로 > 소스명 순.
function citationLabel(c: Citation): string {
  if (c.path) return c.lines ? `${c.path}:${c.lines[0]}-${c.lines[1]}` : c.path;
  return c.sourceName;
}

function CitationChips({ citations }: { citations: Citation[] }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {citations.map((c, i) => (
        <CitationChip key={`${c.sourceId}-${i}`} index={i + 1} label={citationLabel(c)} />
      ))}
    </div>
  );
}

// 보류/추가요청 등 안내 박스.
function Notice({ icon, children }: { icon: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-2 rounded-xl border border-border bg-secondary/40 p-3 text-[13px] leading-relaxed text-muted-foreground">
      <Icon name={icon} size={16} className="mt-0.5 shrink-0" />
      <span>{children}</span>
    </div>
  );
}

// 채팅 답변 렌더(D7). kind별 스텁. 실제 연동 시 백엔드 답변 그래프 출력을 그대로 받는다.
export function AgentMessage({ response }: { response: AgentResponse }) {
  switch (response.kind) {
    case "answer": // lookup: 본문 + 인용칩
      return (
        <div className="space-y-3">
          <p className="text-[13px] leading-relaxed">{response.text}</p>
          <CitationChips citations={response.citations} />
        </div>
      );

    case "references": // locate: 파일/위치 목록
      return (
        <div className="space-y-2">
          {response.intro ? (
            <p className="text-[13px] leading-relaxed text-muted-foreground">{response.intro}</p>
          ) : null}
          <ul className="space-y-1">
            {response.citations.map((c, i) => (
              <li
                key={`${c.sourceId}-${i}`}
                className="flex items-center gap-2 rounded-lg border border-border px-2.5 py-1.5 text-[12px]"
              >
                <Icon name="description" size={14} className="shrink-0 text-muted-foreground" />
                <span className="truncate">{citationLabel(c)}</span>
              </li>
            ))}
          </ul>
        </div>
      );

    case "summary": // summarize: 문단 요약
      return (
        <div className="space-y-3">
          <p className="text-[13px] leading-relaxed">{response.text}</p>
          {response.citations?.length ? <CitationChips citations={response.citations} /> : null}
        </div>
      );

    case "abstain": // 근거 부족 등으로 답변 보류
      return <Notice icon="report">{response.reason}</Notice>;

    case "clarify": // 추가 정보 요청
      return <Notice icon="chat_bubble_outline">{response.question}</Notice>;
  }
}
