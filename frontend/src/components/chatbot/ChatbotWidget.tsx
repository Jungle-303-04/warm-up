import {useState} from 'react';
import {ChatbotWindow} from './ChatbotWindow';
import './chatbot.css';

export function ChatbotWidget() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        className="chatbot-fab"
        onClick={() => setIsOpen(true)}
        aria-label="AI 챗봇 열기"
      >
        AI
      </button>

      {isOpen && (
        <div className="chatbot-backdrop" onClick={() => setIsOpen(false)}>
          <div
            className="chatbot-panel"
            onClick={(event) => event.stopPropagation()}
          >
            <ChatbotWindow onClose={() => setIsOpen(false)} />
          </div>
        </div>
      )}
    </>
  );
}
