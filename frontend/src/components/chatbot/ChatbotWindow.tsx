type ChatbotWindowProps = {
  onClose: () => void;
};

export function ChatbotWindow({onClose}: ChatbotWindowProps) {
  return (
    <div className="chatbot-window">
      <header className="chatbot-header">
        <div>
          <strong>TeamLog AI</strong>
          <p>회의/회고 기반 챗봇</p>
        </div>

        <button onClick={onClose}>×</button>
      </header>

      <main className="chatbot-body">
        <div className="chatbot-welcome-card">
          <strong>무엇이 궁금한가요?</strong>
          <p>저장된 회의와 회고를 기반으로 답변해드릴게요.</p>
        </div>

        {/* 메시지 목록 */}
      </main>

      <footer className="chatbot-input-area">{/* 입력창 */}</footer>
    </div>
  );
}
