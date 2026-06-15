import ProposalsBoard from "./proposals-board";

export default function Home() {
  return (
    <main>
      <section className="shell">
        <p className="eyebrow">RepoPilot</p>
        <h1>코드 기반 제안 검토 보드</h1>
        <p className="summary">
          RepoPilot이 코드와 문서를 분석해 만든 제안을 검토합니다. 대기 중인 제안을
          승인하거나 반려하면 상태가 기록됩니다. 데이터는 백엔드 API에서 실시간으로
          불러옵니다.
        </p>
        <ProposalsBoard />
      </section>
    </main>
  );
}
