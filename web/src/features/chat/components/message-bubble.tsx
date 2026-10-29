import { Bot, Paperclip } from "lucide-react";
import { Spinner } from "@/components/common/spinner";
import { cn } from "@/lib/utils";
import type { Attachment, MessageRole } from "../types";

interface MessageBubbleProps {
  role: MessageRole;
  content: string;
  attachments?: Attachment[];
  isStreaming?: boolean;
}

export function MessageBubble({ role, content, attachments, isStreaming }: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={cn("flex gap-3", isUser && "justify-end")}>
      {!isUser && (
        <span className="mt-0.5 inline-flex size-7 shrink-0 items-center justify-center rounded-full bg-secondary">
          <Bot className="size-4" />
        </span>
      )}
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap",
          isUser ? "bg-primary text-primary-foreground" : "bg-muted",
        )}
      >
        {content ||
          (isStreaming ? (
            <Spinner className="text-muted-foreground" />
          ) : (
            // Backend hiện chưa nối LLM nên assistant message có content rỗng
            <span className="text-muted-foreground italic">(Chưa có phản hồi — backend chưa kết nối LLM)</span>
          ))}

        {attachments && attachments.length > 0 && (
          <ul className="mt-2 grid gap-1">
            {attachments.map((a) => (
              <li key={a.id} className="flex items-center gap-1.5 text-xs opacity-80">
                <Paperclip className="size-3" />
                <a href={a.file_url} target="_blank" rel="noreferrer" className="underline-offset-2 hover:underline">
                  {a.file_name}
                </a>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
