import { Bot } from "lucide-react";
import type { AIModelPublic } from "@/features/ai-models";
import { cn } from "@/lib/utils";

interface ModelSelectProps {
  models: AIModelPublic[];
  value: string | undefined;
  onChange: (modelId: string) => void;
  disabled?: boolean;
  className?: string;
}

/** Chọn model AI cho cuộc trò chuyện — chỉ liệt kê model đang bật (GET /ai-models) */
export function ModelSelect({ models, value, onChange, disabled, className }: ModelSelectProps) {
  // Conversation cũ có thể trỏ tới model đã bị admin tắt → không có trong danh sách
  const isUnavailable = !!value && !models.some((m) => m.id === value);

  return (
    <label className={cn("flex items-center gap-2 text-sm", className)}>
      <Bot className="text-muted-foreground size-4 shrink-0" aria-hidden />
      <span className="sr-only">Model AI</span>
      <select
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled || models.length === 0}
        className={cn(
          "border-input focus-visible:ring-ring h-8 max-w-56 rounded-md border bg-transparent px-2 text-sm outline-none focus-visible:ring-2 disabled:cursor-not-allowed disabled:opacity-50",
          isUnavailable && "border-destructive text-destructive",
        )}
      >
        {models.length === 0 && <option value="">Chưa có model</option>}
        {isUnavailable && (
          <option value={value} disabled>
            Model đã bị tắt
          </option>
        )}
        {models.map((m) => (
          <option key={m.id} value={m.id}>
            {m.display_name} ({m.provider}){m.is_default ? " · mặc định" : ""}
          </option>
        ))}
      </select>
    </label>
  );
}
