type ChatInputProps = {
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
  onSend: () => void;
};

export function ChatInput({value, disabled, onChange, onSend}: ChatInputProps) {
  return (
    <div className="chatbot-input-wrap">
      <textarea
        className="chatbot-input"
        placeholder="회의/회고에 대해 질문하세요..."
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            onSend();
          }
        }}
      />

      <button
        className="chatbot-send-button"
        disabled={disabled || !value.trim()}
        onClick={onSend}
      >
        전송
      </button>
    </div>
  );
}
