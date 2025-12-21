import { useState, FormEvent, useRef, forwardRef, useImperativeHandle } from "react";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled: boolean;
  isLoading: boolean;
}

export interface ChatInputRef {
  focus: () => void;
}

export const ChatInput = forwardRef<ChatInputRef, ChatInputProps>(({
  onSendMessage,
  disabled,
  isLoading,
}, ref) => {
  const [inputValue, setInputValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useImperativeHandle(ref, () => ({
    focus: () => {
      inputRef.current?.focus();
    },
  }));

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !disabled && !isLoading) {
      onSendMessage(inputValue);
      setInputValue("");
    }
  };

  return (
    <form className="chat-input" onSubmit={handleSubmit}>
      <input
        ref={inputRef}
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        placeholder={
          disabled
            ? "Select a user to start chatting..."
            : isLoading
            ? "Waiting for response..."
            : "Type your message..."
        }
        disabled={disabled || isLoading}
      />
      <button type="submit" disabled={disabled || isLoading || !inputValue.trim()}>
        {isLoading ? "Sending..." : "Send"}
      </button>
    </form>
  );
});
