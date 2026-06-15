"use client";

import { useState } from "react";

import { AuthMenu } from "./auth-menu";
import { Icon } from "./icon";
import { MarkdownView } from "./markdown-view";
import { generateProposals, publishProposal } from "../lib/api";

// ── 더미 데이터 ─────────────────────────────────────────────────────
type Source = {
  id: string;
  name: string;
  kind: "repo" | "doc" | "link";
  progress: number;
  status?: string;
};

const SOURCES: Source[] = [
  { id: "a", name: "team/api", kind: "repo", progress: 100 },
  { id: "b", name: "team/web", kind: "repo", progress: 41, status: "동기화중" },
  { id: "c", name: "docs/architecture.md", kind: "doc", progress: 100 },
  { id: "d", name: "wiki.team.dev/onboarding", kind: "link", progress: 100 },
];

const THREADS = ["인증 흐름 점검", "스프린트 계획", "ERD 리뷰"];

const SUGGESTIONS = [
  "이 저장소들의 인증 흐름을 요약해줘",
  "최근 브랜치에서 바뀐 핵심 로직은?",
  "문서와 코드가 어긋난 부분을 찾아줘",
];

const STUDIO_TILES = [
  { icon: "account_tree", label: "UML" },
  { icon: "schema", label: "ERD" },
  { icon: "checklist", label: "계획" },
  { icon: "calendar_month", label: "일정 요약" },
];

const SOURCE_ICON: Record<Source["kind"], string> = {
  repo: "folder_code",
  doc: "description",
  link: "link",
};

const SOURCE_LABEL: Record<Source["kind"], string> = {
  repo: "GitHub 저장소",
  doc: "파일",
  link: "링크",
};

const SAMPLE_DOC = `# docs/architecture.md

팀 저장소를 인덱싱해 **근거 기반**으로 답하고 제안하는 워크스페이스입니다.

## 인증 흐름

1. 클라이언트가 \`POST /api/auth/login\` 호출
2. 서버가 자격 증명 검증 후 **HttpOnly JWT 쿠키** 발급
3. 이후 요청은 쿠키의 토큰으로 인증

> 만료 토큰은 인증 미들웨어에서 \`401\`로 처리됩니다.

### 검색 파이프라인

\`\`\`python
def search(query: str) -> list[Chunk]:
    vec = embed(query)
    return store.hybrid_search(vec, query)  # 벡터 + 키워드 융합
\`\`\`

| 단계 | 설명 |
| --- | --- |
| 청킹 | 심볼 단위 + 마크다운 섹션 |
| 임베딩 | OpenAI / 결정론적 |
| 검색 | pgvector 하이브리드 |

자세한 내용은 [README](#)를 참고하세요.
`;

// ── 작은 조립 단위 ──────────────────────────────────────────────────
function HeaderIcon({ name, label }: { name: string; label: string }) {
  return (
    <button
      type="button"
      title={label}
      className="grid h-8 w-8 place-items-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
    >
      <Icon name={name} className="text-[18px]" />
    </button>
  );
}

function Checkbox({ checked }: { checked: boolean }) {
  return (
    <span
      className={`grid h-4 w-4 place-items-center rounded-[4px] border transition-colors ${
        checked
          ? "border-primary bg-primary text-primary-foreground"
          : "border-input text-transparent"
      }`}
    >
      <Icon name="check" className="text-[12px]" />
    </span>
  );
}

function SourceRow({
  source,
  checked,
  onToggle,
}: {
  source: Source;
  checked: boolean;
  onToggle: () => void;
}) {
  const done = source.progress >= 100;
  return (
    <button
      type="button"
      onClick={onToggle}
      className="group flex w-full items-center gap-2.5 rounded-lg px-2 py-1.5 text-left transition-colors hover:bg-secondary"
    >
      <span className="grid h-7 w-7 shrink-0 place-items-center rounded-md bg-secondary text-muted-foreground group-hover:bg-card">
        <Icon name={SOURCE_ICON[source.kind]} className="text-[16px]" />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-[13px] leading-tight">{source.name}</span>
        <span className="mt-0.5 flex items-center gap-1 text-[11px] text-muted-foreground">
          <span>{SOURCE_LABEL[source.kind]}</span>
          {done ? null : (
            <>
              <span aria-hidden>·</span>
              <span className="h-[3px] w-10 overflow-hidden rounded-full bg-border">
                <span
                  className="block h-full rounded-full bg-primary"
                  style={{ width: `${source.progress}%` }}
                />
              </span>
              <span>{source.progress}%</span>
            </>
          )}
        </span>
      </span>
      <Checkbox checked={checked} />
    </button>
  );
}

function CitationChip({ index, label }: { index: number; label: string }) {
  return (
    <button
      type="button"
      title={label}
      className="inline-flex items-center gap-1 rounded-md bg-secondary px-1.5 py-0.5 text-[11px] text-muted-foreground transition-colors hover:text-foreground"
    >
      <span className="grid h-4 w-4 place-items-center rounded bg-primary/10 text-[10px] font-medium text-primary">
        {index}
      </span>
      {label}
    </button>
  );
}

function ProposalCard() {
  const [decision, setDecision] = useState<"none" | "approved" | "rejected">("none");
  const [repo, setRepo] = useState("");
  const [issue, setIssue] = useState("");
  const [publishing, setPublishing] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; text: string } | null>(null);

  const canPublish = repo.trim().includes("/") && /^\d+$/.test(issue.trim()) && !publishing;

  const onPublish = async () => {
    setPublishing(true);
    setResult(null);
    try {
      const [proposal] = await generateProposals(repo.trim());
      if (!proposal) throw new Error("생성된 제안이 없습니다");
      const url = await publishProposal(proposal.id, Number(issue.trim()));
      setResult({ ok: true, text: url });
    } catch (cause) {
      setResult({ ok: false, text: cause instanceof Error ? cause.message : "알 수 없는 오류" });
    } finally {
      setPublishing(false);
    }
  };

  return (
    <div className="rounded-2xl border border-border bg-card p-4">
      <div className="flex items-center gap-1.5 text-[12px] text-muted-foreground">
        <Icon name="auto_awesome" className="text-[16px] text-primary" />
        제안 · 관련 코드
        <span className="ml-auto text-muted-foreground">confidence 0.86</span>
      </div>
      <p className="mt-2 text-[14px] leading-relaxed">
        <code className="rounded bg-secondary px-1 py-0.5 text-[13px]">docs/auth.md</code> 가 토큰
        만료 케이스를 다루지 않습니다. 인증 미들웨어의 401 처리를 문서에 반영하길 제안합니다.
      </p>

      {decision === "none" ? (
        <div className="mt-3 flex items-center gap-2">
          <button
            type="button"
            onClick={() => setDecision("approved")}
            className="rounded-lg bg-primary px-3.5 py-1.5 text-[13px] font-medium text-primary-foreground transition-opacity hover:opacity-90"
          >
            승인
          </button>
          <button
            type="button"
            onClick={() => setDecision("rejected")}
            className="rounded-lg border border-border px-3.5 py-1.5 text-[13px] text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          >
            반려
          </button>
        </div>
      ) : decision === "rejected" ? (
        <p className="mt-3 text-[13px] text-muted-foreground">반려됨</p>
      ) : (
        <div className="mt-3 space-y-2">
          <p className="text-[12px] text-muted-foreground">승인됨 · GitHub 이슈에 발행</p>
          <div className="flex flex-wrap items-center gap-2">
            <input
              value={repo}
              onChange={(e) => setRepo(e.target.value)}
              placeholder="owner/repo"
              className="w-40 rounded-md border border-input bg-secondary px-2 py-1 text-[12px] outline-none placeholder:text-muted-foreground"
            />
            <input
              value={issue}
              onChange={(e) => setIssue(e.target.value)}
              placeholder="이슈 #"
              inputMode="numeric"
              className="w-20 rounded-md border border-input bg-secondary px-2 py-1 text-[12px] outline-none placeholder:text-muted-foreground"
            />
            <button
              type="button"
              onClick={onPublish}
              disabled={!canPublish}
              className="inline-flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 text-[12px] font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              <Icon name="north_east" className="text-[14px]" />
              {publishing ? "발행 중…" : "GitHub에 발행"}
            </button>
          </div>
          {result ? (
            result.ok ? (
              <a
                href={result.text}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-[12px] text-primary underline"
              >
                <Icon name="check_circle" className="text-[14px]" /> 발행됨 — 코멘트 열기
              </a>
            ) : (
              <p className="text-[12px] text-destructive">⚠ {result.text}</p>
            )
          ) : null}
        </div>
      )}
    </div>
  );
}

// ── 패널 ────────────────────────────────────────────────────────────
function SourcesPanel() {
  const init = Object.fromEntries(SOURCES.map((s) => [s.id, true]));
  const [selected, setSelected] = useState<Record<string, boolean>>(init);
  const allOn = SOURCES.every((s) => selected[s.id]);
  return (
    <aside className="flex w-[320px] shrink-0 flex-col overflow-hidden rounded-2xl border border-border bg-card">
      <div className="flex items-center justify-between px-3 pt-3">
        <h2 className="text-[14px] font-semibold">소스</h2>
        <div className="flex items-center">
          <HeaderIcon name="add" label="소스 추가" />
          <HeaderIcon name="travel_explore" label="탐색" />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-2 pt-1.5">
        <button
          type="button"
          onClick={() =>
            setSelected(Object.fromEntries(SOURCES.map((s) => [s.id, !allOn])))
          }
          className="flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-[12px] text-muted-foreground transition-colors hover:bg-secondary"
        >
          모든 소스 선택
          <Checkbox checked={allOn} />
        </button>
        <div className="mt-1 space-y-0.5">
          {SOURCES.map((s) => (
            <SourceRow
              key={s.id}
              source={s}
              checked={!!selected[s.id]}
              onToggle={() => setSelected((p) => ({ ...p, [s.id]: !p[s.id] }))}
            />
          ))}
        </div>

        <div className="mt-3 px-2">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            대화
          </p>
        </div>
        <div className="mt-1 space-y-0.5">
          {THREADS.map((t) => (
            <button
              key={t}
              type="button"
              className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-[13px] transition-colors hover:bg-secondary"
            >
              <Icon name="chat_bubble_outline" className="text-[16px] text-muted-foreground" />
              <span className="flex-1 truncate">{t}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="border-t border-border p-3">
        <button
          type="button"
          className="flex w-full items-center justify-center gap-1.5 rounded-full border border-border py-2 text-[13px] text-foreground transition-colors hover:bg-secondary"
        >
          <Icon name="add" className="text-[18px]" /> 새 대화
        </button>
      </div>
    </aside>
  );
}

const TABS = ["대화", "보드", "뷰어"] as const;

function ChatPanel() {
  const [tab, setTab] = useState<(typeof TABS)[number]>("대화");
  return (
    <section className="flex flex-1 flex-col overflow-hidden rounded-2xl border border-border bg-card">
      <div className="flex h-12 shrink-0 items-center gap-1 border-b border-border px-3">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded-full px-2.5 py-1 text-[13px] transition-colors ${
              tab === t
                ? "bg-secondary font-semibold text-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "뷰어" ? (
        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-2xl px-5 py-6">
            <div className="mb-4 flex items-center gap-2 text-[12px] text-muted-foreground">
              <Icon name="description" className="text-[16px] text-primary" />
              docs/architecture.md
            </div>
            <article className="markdown-body border-y border-border py-5 text-[14px] leading-relaxed">
              <MarkdownView source={SAMPLE_DOC} />
            </article>
          </div>
        </div>
      ) : tab === "보드" ? (
        <div className="grid flex-1 place-items-center text-[13px] text-muted-foreground">
          보드 — 추후 구현
        </div>
      ) : (
        <>
          <div className="flex-1 overflow-y-auto">
            <div className="mx-auto w-full max-w-2xl px-5 py-6">
              {/* 요약 카드 (NotebookLM 시그니처) */}
              <div className="rounded-2xl border border-border bg-secondary/50 p-4">
                <div className="flex items-center gap-2.5">
                  <span className="grid h-9 w-9 place-items-center rounded-xl bg-primary/10 text-primary">
                    <Icon name="hub" className="text-[20px]" />
                  </span>
                  <div className="min-w-0">
                    <h1 className="truncate text-[15px] font-semibold">team 워크스페이스</h1>
                    <p className="text-[11px] text-muted-foreground">
                      소스 4개 · 모든 브랜치 인덱싱
                    </p>
                  </div>
                </div>
                <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">
                  연결된 저장소·문서를 근거로 질문에 답하고, 코드와 문서가 어긋난 부분을
                  찾아 제안합니다. 답변에는 항상 출처(파일·라인·커밋)가 따라옵니다.
                </p>
              </div>

              {/* 추천 질문 */}
              <div className="mt-4 space-y-1.5">
                {SUGGESTIONS.map((q) => (
                  <button
                    key={q}
                    type="button"
                    className="flex w-full items-center gap-2.5 rounded-xl border border-border px-3 py-2 text-left text-[13px] text-foreground transition-colors hover:bg-secondary"
                  >
                    <Icon name="add_circle" className="text-[16px] text-muted-foreground" />
                    <span className="flex-1">{q}</span>
                  </button>
                ))}
              </div>

              {/* 대화 예시 */}
              <div className="mt-6 space-y-3">
                <p className="text-[13px] leading-relaxed">
                  로그인 실패는 JWT 만료가 가장 흔한 원인입니다. 인증 미들웨어가 만료 토큰을
                  401로 처리합니다.
                </p>
                <div className="flex flex-wrap gap-1.5">
                  <CitationChip index={1} label="api/auth.py:12-18" />
                  <CitationChip index={2} label="docs/auth.md" />
                </div>
                <ProposalCard />
              </div>
            </div>
          </div>

          <div className="shrink-0 px-4 pb-4">
            <div className="mx-auto flex max-w-2xl items-end gap-2 rounded-2xl border border-border bg-secondary px-3.5 py-2.5">
              <textarea
                rows={1}
                placeholder="무엇이든 물어보세요"
                className="max-h-28 flex-1 resize-none bg-transparent text-[13px] leading-relaxed outline-none placeholder:text-muted-foreground"
              />
              <button
                type="button"
                className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-primary text-primary-foreground transition-opacity hover:opacity-90"
              >
                <Icon name="arrow_upward" className="text-[18px]" />
              </button>
            </div>
            <p className="mx-auto mt-1.5 max-w-2xl text-center text-[11px] text-muted-foreground">
              RepoLM의 답변은 부정확할 수 있으니 출처를 확인하세요.
            </p>
          </div>
        </>
      )}
    </section>
  );
}

function StudioPanel() {
  return (
    <aside className="flex w-[300px] shrink-0 flex-col overflow-hidden rounded-2xl border border-border bg-card">
      <div className="flex items-center justify-between px-3 pt-3">
        <h2 className="text-[14px] font-semibold">스튜디오</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-3">
        <div className="grid grid-cols-3 gap-2">
          {STUDIO_TILES.map((t) => (
            <button
              key={t.label}
              type="button"
              className="flex flex-col items-center gap-1.5 rounded-xl border border-border bg-secondary/50 px-2 py-3 text-center transition-colors hover:border-primary"
            >
              <Icon name={t.icon} className="text-[20px] text-primary" />
              <span className="text-[11px] font-medium leading-tight">{t.label}</span>
            </button>
          ))}
        </div>

        <div className="mt-5 flex items-center justify-between">
          <p className="text-[13px] font-semibold">메모</p>
          <button
            type="button"
            className="inline-flex items-center gap-1 rounded-full border border-border px-2.5 py-1 text-[12px] text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          >
            <Icon name="add" className="text-[16px]" /> 추가
          </button>
        </div>
        <div className="mt-2 space-y-2">
          {["도메인 ERD v2", "인증 시퀀스 UML"].map((n) => (
            <button
              key={n}
              type="button"
              className="flex w-full items-center gap-2 rounded-xl border border-border bg-secondary/40 px-3 py-2.5 text-left text-[13px] transition-colors hover:bg-secondary"
            >
              <Icon name="article" className="text-[18px] text-muted-foreground" />
              <span className="flex-1 truncate">{n}</span>
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}

function TopBar() {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between px-4">
      <div className="flex items-center gap-2">
        <Icon name="hub" className="text-[22px] text-primary" />
        <span className="text-[15px] font-semibold">RepoLM</span>
        <Icon name="chevron_right" className="text-[18px] text-muted-foreground" />
        <button
          type="button"
          className="inline-flex items-center gap-1 rounded-md px-1.5 py-1 text-[14px] text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
        >
          team 워크스페이스
          <Icon name="unfold_more" className="text-[16px]" />
        </button>
      </div>
      <div className="flex items-center gap-1">
        <button
          type="button"
          className="mr-1 inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-[13px] text-muted-foreground transition-colors hover:bg-secondary"
        >
          <Icon name="share" className="text-[16px]" /> 공유
        </button>
        <HeaderIcon name="notifications" label="알림" />
        <AuthMenu />
      </div>
    </header>
  );
}

export function Workspace() {
  return (
    <div className="flex h-screen flex-col bg-background text-foreground">
      <TopBar />
      <main className="flex flex-1 gap-3 overflow-hidden px-3 pb-3">
        <SourcesPanel />
        <ChatPanel />
        <StudioPanel />
      </main>
    </div>
  );
}
