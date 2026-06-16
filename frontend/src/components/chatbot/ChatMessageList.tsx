import type {ChatReference} from '../../api/chat';

export type LocalChatMessage = {
  role: 'user' | 'assistant';
  content: string;
  references?: ChatReference[];
};

type ChatMessageListProps = {
  messages: LocalChatMessage[];
  isLoading: boolean;
};

export function ChatMessageList({messages, isLoading}: ChatMessageListProps) {
  return (
    <div className="chatbot-message-list">
      {messages.length === 0 && (
        <div className="chatbot-welcome-card">
          <strong>무엇이 궁금한가요?</strong>
          <p>저장된 회의와 회고를 기반으로 답변해드릴게요.</p>
        </div>
      )}

      {messages.map((message, index) => (
        <div
          key={`${message.role}-${index}`}
          className={
            message.role === 'user'
              ? 'chatbot-message chatbot-message-user'
              : 'chatbot-message chatbot-message-assistant'
          }
        >
          <p>{message.content}</p>

          {message.role === 'assistant' &&
            message.references &&
            message.references.length > 0 && (
              <div className="chatbot-references">
                <strong>참고 기록</strong>
                {message.references.map((reference) => (
                  <div
                    key={`${reference.page_id}-${reference.chunk_index ?? 0}`}
                    className="chatbot-reference-item"
                  >
                    {reference.title}
                    {reference.date ? ` / ${reference.date}` : ''}
                  </div>
                ))}
              </div>
            )}
        </div>
      ))}

      {isLoading && (
        <div className="chatbot-message chatbot-message-assistant">
          <p>답변을 생성하는 중...</p>
        </div>
      )}
    </div>
  );
}
