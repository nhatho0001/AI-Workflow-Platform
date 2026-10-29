// Khớp với server/app/modules/chat_core/schemas.py

export type MessageRole = "user" | "assistant" | "system" | "tool";

export interface Attachment {
  id: string;
  message_id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  file_url: string;
  created_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  parent_message_id: string | null;
  model_id: string | null;
  role: MessageRole;
  content: string;
  metadata: Record<string, unknown> | null;
  token_count: number;
  finish_reason: string | null;
  created_at: string;
  attachments: Attachment[];
}

export interface Conversation {
  id: string;
  user_id: string;
  model_id: string;
  folder_id: string | null;
  title: string | null;
  system_prompt: string | null;
  temperature: number | null;
  is_archived: boolean;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[];
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ListConversationsParams {
  page?: number;
  page_size?: number;
  is_archived?: boolean;
  folder_id?: string;
}

export type ConversationUpdate = Partial<
  Pick<Conversation, "title" | "system_prompt" | "temperature" | "folder_id" | "is_archived" | "is_pinned" | "model_id">
>;

export interface ChatStartRequest {
  model_id: string;
  message: string;
  folder_id?: string | null;
  title?: string | null;
  system_prompt?: string | null;
  temperature?: number | null;
}

export interface ChatMessageInput {
  content: string;
  parent_message_id?: string | null;
  metadata?: Record<string, unknown> | null;
}

// Các event SSE mà chat_core/router.py phát ra (`data: {"event": ..., "data": ...}`)
export type ChatStreamEvent =
  | { event: "conversation_created"; data: { conversation_id: string; user_message_id: string } }
  | { event: "user_message_saved"; data: { user_message_id: string } }
  | { event: "delta"; data: { content: string } }
  | {
      event: "message_done";
      data: { assistant_message_id: string; token_count: number; finish_reason: string };
    };
