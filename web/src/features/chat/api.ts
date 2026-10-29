import { apiClient } from "@/lib/api-client";
import { streamSSE } from "@/lib/sse";
import type {
  ChatMessageInput,
  ChatStartRequest,
  ChatStreamEvent,
  Conversation,
  ConversationUpdate,
  ConversationWithMessages,
  ListConversationsParams,
  Paginated,
} from "./types";

export const chatApi = {
  listConversations: (params: ListConversationsParams = {}) =>
    apiClient.get<Paginated<Conversation>>("/chat/conversations", { params }).then((r) => r.data),

  getConversationFull: (id: string) =>
    apiClient.get<ConversationWithMessages>(`/chat/conversations/${id}/full`).then((r) => r.data),

  updateConversation: (id: string, body: ConversationUpdate) =>
    apiClient.patch<Conversation>(`/chat/conversations/${id}`, body).then((r) => r.data),

  togglePin: (id: string) => apiClient.post<Conversation>(`/chat/conversations/${id}/pin`).then((r) => r.data),

  toggleArchive: (id: string) =>
    apiClient.post<Conversation>(`/chat/conversations/${id}/archive`).then((r) => r.data),

  deleteConversation: (id: string) => apiClient.delete(`/chat/conversations/${id}`).then(() => undefined),

  // ── Streaming ──────────────────────────────────────────────────────
  startChat: (body: ChatStartRequest, onEvent: (e: ChatStreamEvent) => void, signal?: AbortSignal) =>
    streamSSE<ChatStreamEvent>({ path: "/chat/start", body, onEvent, signal }),

  sendMessage: (
    conversationId: string,
    body: ChatMessageInput,
    onEvent: (e: ChatStreamEvent) => void,
    signal?: AbortSignal,
  ) =>
    streamSSE<ChatStreamEvent>({
      path: `/chat/conversations/${conversationId}/messages`,
      body,
      onEvent,
      signal,
    }),
};
