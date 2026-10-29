import { ArrowUp, Square } from "lucide-react";
import { useState, type FormEvent, type KeyboardEvent } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

const MAX_LENGTH = 2000; // ChatMessageInput.content max_length ở backend

interface ChatComposerProps {
  onSend: (content: string) => void;
  onStop: () => void;
  isStreaming: boolean;
}

export function ChatComposer({ onSend, onStop, isStreaming }: ChatComposerProps) {
  const [value, setValue] = useState("");
  const trimmed = value.trim();

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    if (!trimmed || isStreaming) return;
    onSend(trimmed);
    setValue("");
  };

  // Enter để gửi, Shift+Enter xuống dòng
  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <form onSubmit={submit} className="relative mx-auto w-full max-w-3xl">
      <Textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={onKeyDown}
        maxLength={MAX_LENGTH}
        rows={3}
        placeholder="Nhập tin nhắn… (Enter để gửi, Shift+Enter xuống dòng)"
        className="resize-none rounded-2xl pr-14"
        aria-label="Tin nhắn"
      />
      {isStreaming ? (
        <Button size="icon" variant="secondary" className="absolute right-3 bottom-3 rounded-full" onClick={onStop} aria-label="Dừng">
          <Square />
        </Button>
      ) : (
        <Button
          type="submit"
          size="icon"
          className="absolute right-3 bottom-3 rounded-full"
          disabled={!trimmed}
          aria-label="Gửi"
        >
          <ArrowUp />
        </Button>
      )}
    </form>
  );
}
