import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { env } from "@/config/env";
import { getErrorMessage } from "@/lib/api-client";
import { chatApi } from "./api";
import type { ChatStreamEvent, ListConversationsParams } from "./types";

export const chatKeys = {
  all: ["chat"] as const,
  conversations: (params: ListConversationsParams) => [...chatKeys.all, "conversations", params] as const,
  conversation: (id: string) => [...chatKeys.all, "conversation", id] as const,
};

export function useConversations(params: ListConversationsParams = {}) {
  return useQuery({
    queryKey: chatKeys.conversations(params),
    queryFn: () => chatApi.listConversations(params),
  });
}

export function useConversation(id: string | undefined) {
  return useQuery({
    queryKey: chatKeys.conversation(id ?? ""),
    queryFn: () => chatApi.getConversationFull(id!),
    enabled: Boolean(id),
    select: (data) => ({
      ...data,
      messages: [...data.messages].sort((a, b) => a.created_at.localeCompare(b.created_at)),
    }),
  });
}

function useInvalidateChat() {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: chatKeys.all });
}

export function useTogglePin() {
  const invalidate = useInvalidateChat();
  return useMutation({ mutationFn: chatApi.togglePin, onSuccess: invalidate });
}

export function useToggleArchive() {
  const invalidate = useInvalidateChat();
  return useMutation({ mutationFn: chatApi.toggleArchive, onSuccess: invalidate });
}

export function useRenameConversation() {
  const invalidate = useInvalidateChat();
  return useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) => chatApi.updateConversation(id, { title }),
    onSuccess: invalidate,
  });
}

export function useDeleteConversation() {
  const invalidate = useInvalidateChat();
  return useMutation({ mutationFn: chatApi.deleteConversation, onSuccess: invalidate });
}

// ── Streaming chat ─────────────────────────────────────────────────────

interface UseChatStreamOptions {
  conversationId?: string;
  /** Gọi khi /chat/start tạo xong conversation mới — dùng để điều hướng sang URL của nó */
  onConversationCreated?: (conversationId: string) => void;
}

export function useChatStream({ conversationId, onConversationCreated }: UseChatStreamOptions) {
  const queryClient = useQueryClient();
  const abortRef = useRef<AbortController | null>(null);

  const [isStreaming, setIsStreaming] = useState(false);
  const [pendingUserMessage, setPendingUserMessage] = useState<string | null>(null);
  // id thật của user message vừa gửi — để trang lọc bản trùng khi query tải lại giữa chừng
  const [pendingUserMessageId, setPendingUserMessageId] = useState<string | null>(null);
  const [streamingContent, setStreamingContent] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Conversation vừa được tạo bởi stream hiện tại — URL đổi sang id này thì không huỷ stream
  const createdIdRef = useRef<string | null>(null);

  // Huỷ stream khi rời trang hoặc chuyển sang conversation khác
  useEffect(() => () => abortRef.current?.abort(), []);
  useEffect(() => {
    if (conversationId !== createdIdRef.current) abortRef.current?.abort();
  }, [conversationId]);

  const send = useCallback(
    async (content: string) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setIsStreaming(true);
      setError(null);
      setPendingUserMessage(content);
      setStreamingContent("");

      let targetId = conversationId;
      const onEvent = (e: ChatStreamEvent) => {
        switch (e.event) {
          case "conversation_created":
            targetId = e.data.conversation_id;
            createdIdRef.current = targetId;
            setPendingUserMessageId(e.data.user_message_id);
            onConversationCreated?.(targetId);
            break;
          case "user_message_saved":
            setPendingUserMessageId(e.data.user_message_id);
            break;
          case "delta":
            setStreamingContent((prev) => prev + e.data.content);
            break;
        }
      };

      try {
        if (conversationId) {
          await chatApi.sendMessage(conversationId, { content }, onEvent, controller.signal);
        } else {
          await chatApi.startChat({ model_id: env.defaultModelId, message: content }, onEvent, controller.signal);
        }
      } catch (err) {
        if (!controller.signal.aborted) setError(getErrorMessage(err));
      } finally {
        // Đợi dữ liệu mới về rồi mới bỏ bản tạm, tránh nháy giao diện
        if (targetId) await queryClient.invalidateQueries({ queryKey: chatKeys.conversation(targetId) });
        await queryClient.invalidateQueries({ queryKey: [...chatKeys.all, "conversations"] });
        if (abortRef.current === controller) {
          createdIdRef.current = null;
          setIsStreaming(false);
          setPendingUserMessage(null);
          setPendingUserMessageId(null);
          setStreamingContent("");
        }
      }
    },
    [conversationId, onConversationCreated, queryClient],
  );

  const stop = useCallback(() => abortRef.current?.abort(), []);

  return { send, stop, isStreaming, pendingUserMessage, pendingUserMessageId, streamingContent, error };
}
