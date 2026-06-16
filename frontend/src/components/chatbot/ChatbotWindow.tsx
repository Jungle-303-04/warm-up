import {useState} from 'react';
import {sendChatMessage} from '../../api/chat';
import {ChatInput} from './ChatInput';
import {ChatMessageList, type LocalChatMessage} from './ChatMessageList';

type ChatbotWindowProps = {
  onClose: () => void;
};

export function ChatbotWindow({onClose}: ChatbotWindowProps) {
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<LocalChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  async function handleSend() {
    const text = input.trim();

    if (!text || isLoading) {
      return;
    }

    setInput('');

    setMessages((prev) => [
      ...prev,
      {
        role: 'user',
        content: text,
      },
    ]);

    setIsLoading(true);

    try {
      const result = await sendChatMessage({
        sessionId,
        message: text,
      });

      setSessionId(result.session_id);

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: result.message,
          references: result.references,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            '답변 생성 중 오류가 발생했습니다. 로그인 상태나 서버 로그를 확인해 주세요.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="chatbot-window">
      <header className="chatbot-header">
        <div>
          <strong>TeamLog AI</strong>
          <p>회의/회고 기반 챗봇</p>
        </div>

        <button
          className="chatbot-close-button"
          onClick={onClose}
          aria-label="챗봇 닫기"
        >
          ×
        </button>
      </header>

      <ChatMessageList messages={messages} isLoading={isLoading} />

      <ChatInput
        value={input}
        disabled={isLoading}
        onChange={setInput}
        onSend={handleSend}
      />
    </div>
  );
}
