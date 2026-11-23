import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { FormError } from "@/components/common/form-field";
import { Spinner } from "@/components/common/spinner";
import { useEnabledAIModels } from "@/features/ai-models";
import { useCurrentUser } from "@/features/users";
import { getErrorMessage } from "@/lib/api-client";
import { ChatComposer } from "../components/chat-composer";
import { ConversationSidebar } from "../components/conversation-sidebar";
import { MessageBubble } from "../components/message-bubble";
import { ModelSelect } from "../components/model-select";
import { useChatStream, useConversation, useUpdateConversation } from "../hooks";

export function ChatPage() {
  const { conversationId } = useParams<{ conversationId?: string }>();
  const navigate = useNavigate();
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: conversation, isLoading, error: loadError } = useConversation(conversationId);
  const { data: me } = useCurrentUser();
  const { data: models = [], isLoading: modelsLoading, error: modelsError } = useEnabledAIModels();
  const updateConversation = useUpdateConversation();

  // Model cho cuộc trò chuyện MỚI: user chọn, nếu chưa chọn thì lấy model mặc định / model đầu tiên.
  // Cuộc trò chuyện đã có thì luôn dùng conversation.model_id (server cũng dùng giá trị này khi gửi).
  const [pickedModelId, setPickedModelId] = useState<string>();
  const newChatModelId =
    (pickedModelId && models.some((m) => m.id === pickedModelId) ? pickedModelId : undefined) ??
    (models.find((m) => m.is_default) ?? models[0])?.id;
  const activeModelId = conversationId ? conversation?.model_id : newChatModelId;
  const modelAvailable = !!activeModelId && models.some((m) => m.id === activeModelId);

  const onModelChange = (modelId: string) => {
    if (conversationId) updateConversation.mutate({ id: conversationId, body: { model_id: modelId } });
    else setPickedModelId(modelId);
  };

  const onConversationCreated = useCallback(
    (id: string) => navigate(`/chat/${id}`, { replace: true }),
    [navigate],
  );
  const chat = useChatStream({ conversationId, modelId: newChatModelId, onConversationCreated });

  let modelHint: string | null = null;
  if (!modelsLoading && !modelsError && models.length === 0) {
    modelHint =
      me?.role === "admin"
        ? "Chưa có model AI nào được bật. Vào trang “AI models” để thêm model."
        : "Chưa có model AI nào được bật. Hãy liên hệ admin để thêm model.";
  } else if (conversationId && conversation && !modelsLoading && !modelAvailable) {
    modelHint = "Model của cuộc trò chuyện này đã bị tắt. Chọn model khác để tiếp tục.";
  }

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
        <header className="flex items-center justify-between gap-4 border-b px-6 py-3">
          <h1 className="min-w-0 truncate font-medium">
            {conversation?.title || (conversationId ? "Không tiêu đề" : "Cuộc trò chuyện mới")}
          </h1>
          <div className="flex shrink-0 items-center gap-2">
            {updateConversation.isPending && <Spinner />}
            <ModelSelect
              models={models}
              value={activeModelId}
              onChange={onModelChange}
              disabled={
                modelsLoading ||
                chat.isStreaming ||
                updateConversation.isPending ||
                (!!conversationId && !conversation)
              }
            />
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-6 py-6">
          <div className="mx-auto grid max-w-3xl gap-4">
            {isEmpty && (
              <div className="py-24 text-center">
                <h2 className="text-2xl font-semibold">Hôm nay bạn cần hỗ trợ gì?</h2>
                <p className="text-muted-foreground mt-2">
                  Gửi tin nhắn đầu tiên để bắt đầu cuộc trò chuyện.
                </p>
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

        <div className="grid gap-2 border-t px-6 py-4">
          <div className="mx-auto w-full max-w-3xl empty:hidden">
            <FormError
              message={
                modelsError
                  ? getErrorMessage(modelsError)
                  : updateConversation.error
                    ? getErrorMessage(updateConversation.error)
                    : modelHint
              }
            />
          </div>
          <ChatComposer
            onSend={chat.send}
            onStop={chat.stop}
            isStreaming={chat.isStreaming}
            disabled={!modelAvailable || updateConversation.isPending}
          />
        </div>
      </section>
    </div>
  );
}
