import { useCallback, useEffect, useRef } from "react";
import { useNavigate, useParams } from "react-router";
import { FormError } from "@/components/common/form-field";
import { Spinner } from "@/components/common/spinner";
import { getErrorMessage } from "@/lib/api-client";
import { ChatComposer } from "../components/chat-composer";
import { ConversationSidebar } from "../components/conversation-sidebar";
import { MessageBubble } from "../components/message-bubble";
import { useChatStream, useConversation } from "../hooks";

export function ChatPage() {
  const { conversationId } = useParams<{ conversationId?: string }>();
  const navigate = useNavigate();
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: conversation, isLoading, error: loadError } = useConversation(conversationId);

  const onConversationCreated = useCallback(
    (id: string) => navigate(`/chat/${id}`, { replace: true }),
    [navigate],
  );
  const chat = useChatStream({ conversationId, onConversationCreated });

  // Trong lúc stream, ẩn các message đã lưu ở server mà đang được hiển thị dưới dạng bản tạm
  const messages = (conversation?.messages ?? []).filter(
    (m) =>
      !chat.pendingUserMessage ||
      (m.id !== chat.pendingUserMessageId && m.parent_message_id !== chat.pendingUserMessageId),
  );

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, chat.streamingContent, chat.pendingUserMessage]);

  const isEmpty = !conversationId && !chat.pendingUserMessage;

  return (
    <div className="flex min-h-0 flex-1">
      <ConversationSidebar activeId={conversationId} />

      <section className="flex min-w-0 flex-1 flex-col">
        <header className="border-b px-6 py-3">
          <h1 className="truncate font-medium">
            {conversation?.title || (conversationId ? "Không tiêu đề" : "Cuộc trò chuyện mới")}
          </h1>
        </header>

        <div className="flex-1 overflow-y-auto px-6 py-6">
          <div className="mx-auto grid max-w-3xl gap-4">
            {isEmpty && (
              <div className="py-24 text-center">
                <h2 className="text-2xl font-semibold">Hôm nay bạn cần hỗ trợ gì?</h2>
                <p className="mt-2 text-muted-foreground">Gửi tin nhắn đầu tiên để bắt đầu cuộc trò chuyện.</p>
              </div>
            )}

            {isLoading && (
              <div className="flex justify-center py-8">
                <Spinner />
              </div>
            )}
            <FormError message={loadError ? getErrorMessage(loadError) : null} />

            {messages.map((m) => (
              <MessageBubble key={m.id} role={m.role} content={m.content} attachments={m.attachments} />
            ))}

            {chat.pendingUserMessage && (
              <>
                <MessageBubble role="user" content={chat.pendingUserMessage} />
                <MessageBubble role="assistant" content={chat.streamingContent} isStreaming />
              </>
            )}

            <FormError message={chat.error} />
            <div ref={bottomRef} />
          </div>
        </div>

        <div className="border-t px-6 py-4">
          <ChatComposer onSend={chat.send} onStop={chat.stop} isStreaming={chat.isStreaming} />
        </div>
      </section>
    </div>
  );
}
