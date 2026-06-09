const stages = [
  {
    id: "repo-sync",
    name: "Repo Sync",
    detail: "repo, issue, PR, label, milestone metadata"
  },
  {
    id: "code-index",
    name: "Code Index",
    detail: "file, symbol, commit, code reference"
  },
  {
    id: "rag-index",
    name: "RAG Index",
    detail: "docs, issues, PRs, code chunks with permission metadata"
  },
  {
    id: "agent-proposal",
    name: "Agent Proposal",
    detail: "related code, stale links, issue drafts, doc updates"
  },
  {
    id: "approval",
    name: "Approval",
    detail: "human review before GitHub or document writes"
  },
  {
    id: "static-publish",
    name: "Static Publish",
    detail: "read-only static archive with search and filters"
  }
] as const;

export default function Home() {
  return (
    <main>
      <section className="shell">
        <p className="eyebrow">RepoPilot Pipeline</p>
        <h1>문서와 코드의 연결 상태를 추적하는 최소 실행 골격</h1>
        <p className="summary">
          이 화면은 제품 UI가 아니라 로컬 파이프라인이 올라왔는지 확인하는
          시작점입니다. 실제 MVP는 문서, 일감, GitHub 이슈, 코드 참조를 하나의
          프로젝트 모델로 연결합니다.
        </p>
        <ul className="pipeline">
          {stages.map((stage) => (
            <li key={stage.id}>
              <strong>{stage.name}</strong>
              <span>{stage.detail}</span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
