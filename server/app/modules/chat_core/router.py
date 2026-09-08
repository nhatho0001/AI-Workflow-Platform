from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, AsyncGenerator
from uuid import UUID
import json

from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundException, ForbiddenException
from app.modules.users.models import User
from app.modules.chat_core.schemas import (
    # Conversation
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationWithMessagesResponse,
    PaginatedConversations,
    # Message
    MessageResponse,
    MessageUpdate,
    PaginatedMessages,
    # Attachment
    AttachmentResponse,
    # Chat
    ChatRequest,
    ChatMessageInput,
)
from app.modules.chat_core.services import (
    ConversationService,
    MessageService,
    AttachmentService,
    ChatService,
)


# ─────────────────────────────────────────────────────────────────────
# Router setup
# ─────────────────────────────────────────────────────────────────────

router = APIRouter(tags=["Chat"])


# ─────────────────────────────────────────────────────────────────────
# Exception handler helper
# ─────────────────────────────────────────────────────────────────────

def _handle_service_error(exc: Exception) -> None:
    if isinstance(exc, NotFoundException):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, ForbiddenException):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    raise exc


# ═════════════════════════════════════════════════════════════════════
# CONVERSATION ENDPOINTS
# ═════════════════════════════════════════════════════════════════════

@router.get(
    "/conversations",
    response_model=PaginatedConversations,
    summary="Danh sách conversations của user",
)
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_archived: bool = Query(False),
    folder_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await ConversationService.list_by_user(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        is_archived=is_archived,
        folder_id=folder_id,
    )


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo conversation mới (không kèm message)",
)
async def create_conversation(
    payload: ConversationCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await ConversationService.create(
        db=db,
        user_id=current_user.id,
        payload=payload,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="Chi tiết conversation",
)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return await ConversationService.get_by_id(db, conversation_id, current_user.id)
    except (NotFoundException, ForbiddenException) as exc:
        _handle_service_error(exc)


@router.get(
    "/conversations/{conversation_id}/full",
    response_model=ConversationWithMessagesResponse,
    summary="Conversation kèm toàn bộ messages + attachments",
)
async def get_conversation_with_messages(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return await ConversationService.get_with_messages(
            db, conversation_id, current_user.id
        )
    except (NotFoundException, ForbiddenException) as exc:
        _handle_service_error(exc)


@router.patch(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="Cập nhật conversation (title, system_prompt, model, folder…)",
)
async def update_conversation(
    conversation_id: UUID,
    payload: ConversationUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return await ConversationService.update(
            db, conversation_id, current_user.id, payload
        )
    except (NotFoundException, ForbiddenException) as exc:
        _handle_service_error(exc)


@router.post(
    "/conversations/{conversation_id}/archive",
    response_model=ConversationResponse,
    summary="Toggle archive/unarchive",
)
async def toggle_archive(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return await ConversationService.toggle_archive(
            db, conversation_id, current_user.id
        )
    except (NotFoundException, ForbiddenException) as exc:
        _handle_service_error(exc)


@router.post(
    "/conversations/{conversation_id}/pin",
    response_model=ConversationResponse,
    summary="Toggle pin/unpin",
)
async def toggle_pin(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return await ConversationService.toggle_pin(
            db, conversation_id, current_user.id
        )
    except (NotFoundException, ForbiddenException) as exc:
        _handle_service_error(exc)


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa conversation",
)
async def delete_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        await ConversationService.delete(db, conversation_id, current_user.id)
    except (NotFoundException, ForbiddenException) as exc:
        _handle_service_error(exc)


# ═════════════════════════════════════════════════════════════════════
# CHAT — Start & Send (với streaming)
# ═════════════════════════════════════════════════════════════════════

@router.post(
    "/start",
    response_model=None,  # streaming, không dùng response_model
    summary="Tạo conversation mới + stream assistant reply",
)
async def start_chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Tạo conversation mới, lưu user message, sau đó stream response từ LLM.
    Client nhận SSE: `data: <json_chunk>\\n\\n`, kết thúc bằng `data: [DONE]\\n\\n`.
    """
    conversation, user_message = await ChatService.start_chat(
        db=db,
        user_id=current_user.id,
        payload=payload,
    )

    async def event_stream() -> AsyncGenerator[str, None]:
        # Gửi metadata conversation + user_message ngay lập tức
        yield _sse({"event": "conversation_created", "data": {
            "conversation_id": str(conversation.id),
            "user_message_id": str(user_message.id),
        }})

        # ── Gọi LLM ở đây (placeholder — thay bằng LLM client thực) ──
        full_content = ""
        token_count = 0
        finish_reason = "stop"

        # Giả lập stream từ LLM (replace bằng openai/anthropic async stream)
        # async for chunk in llm_client.stream(...):
        #     full_content += chunk.delta
        #     token_count = chunk.usage.total_tokens
        #     finish_reason = chunk.finish_reason or finish_reason
        #     yield _sse({"event": "delta", "data": {"content": chunk.delta}})

        # Sau khi stream xong → lưu assistant message vào DB
        assistant_message = await ChatService.save_assistant_reply(
            db=db,
            conversation_id=conversation.id,
            content=full_content,
            model_id=conversation.model_id,
            parent_message_id=user_message.id,
            token_count=token_count,
            finish_reason=finish_reason,
        )

        yield _sse({"event": "message_done", "data": {
            "assistant_message_id": str(assistant_message.id),
            "token_count": token_count,
            "finish_reason": finish_reason,
        }})
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=None,
    summary="Gửi message vào conversation + stream assistant reply",
)
async def send_message(
    conversation_id: UUID,
    payload: ChatMessageInput,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Gửi user message vào conversation đã có, stream lại assistant reply.
    """
    try:
        user_message = await ChatService.send_message(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
            content=payload.content,
            parent_message_id=payload.parent_message_id,
            metadata=payload.metadata,
        )
    except (NotFoundException, ForbiddenException) as exc:
        _handle_service_error(exc)

    # Lấy conversation để biết model_id
    conversation = await ConversationService.get_by_id(
        db, conversation_id, current_user.id
    )

    async def event_stream() -> AsyncGenerator[str, None]:
        yield _sse({"event": "user_message_saved", "data": {
            "user_message_id": str(user_message.id),
        }})

        # ── Stream LLM (placeholder) ──────────────────────────────
        full_content = ""
        token_count = 0
        finish_reason = "stop"

        # async for chunk in llm_client.stream(...):
        #     full_content += chunk.delta
        #     yield _sse({"event": "delta", "data": {"content": chunk.delta}})

        assistant_message = await ChatService.save_assistant_reply(
            db=db,
            conversation_id=conversation_id,
            content=full_content,
            model_id=conversation.model_id,
            parent_message_id=user_message.id,
            token_count=token_count,
            finish_reason=finish_reason,
        )

        yield _sse({"event": "message_done", "data": {
            "assistant_message_id": str(assistant_message.id),
            "token_count": token_count,
            "finish_reason": finish_reason,
        }})
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ═════════════════════════════════════════════════════════════════════
# MESSAGE ENDPOINTS
# ═════════════════════════════════════════════════════════════════════

@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=PaginatedMessages,
    summary="Danh sách messages trong conversation (paginated)",
)
async def list_messages(
    conversation_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Verify ownership trước khi trả messages
    try:
        await ConversationService.get_by_id(db, conversation_id, current_user.id)
    except (NotFoundException, ForbiddenException) as exc:
        _handle_service_error(exc)

    return await MessageService.list_by_conversation(
        db=db,
        conversation_id=conversation_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/messages/{message_id}",
    response_model=MessageResponse,
    summary="Chi tiết một message",
)
async def get_message(
    message_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return await MessageService.get_by_id(db, message_id)
    except NotFoundException as exc:
        _handle_service_error(exc)


@router.get(
    "/messages/{message_id}/thread",
    response_model=list[MessageResponse],
    summary="Lấy toàn bộ thread từ root → message (branching support)",
)
async def get_message_thread(
    message_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return await MessageService.get_thread(db, message_id)
    except NotFoundException as exc:
        _handle_service_error(exc)


@router.patch(
    "/messages/{message_id}",
    response_model=MessageResponse,
    summary="Cập nhật content hoặc metadata của message",
)
async def update_message(
    message_id: UUID,
    payload: MessageUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return await MessageService.update(db, message_id, payload)
    except NotFoundException as exc:
        _handle_service_error(exc)


@router.delete(
    "/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa message",
)
async def delete_message(
    message_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        await MessageService.delete(db, message_id)
    except NotFoundException as exc:
        _handle_service_error(exc)


# ═════════════════════════════════════════════════════════════════════
# ATTACHMENT ENDPOINTS
# ═════════════════════════════════════════════════════════════════════

@router.post(
    "/messages/{message_id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload attachment cho message",
)
async def upload_attachment(
    message_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Upload file → lưu metadata vào DB.
    Phần lưu file thực tế (S3, local…) cần inject storage service riêng.
    """
    # Verify message tồn tại
    try:
        await MessageService.get_by_id(db, message_id)
    except NotFoundException as exc:
        _handle_service_error(exc)

    # ── Storage logic (placeholder) ─────────────────────
    # file_url = await storage_service.upload(file)
    file_url = f"/uploads/{file.filename}"  # replace với URL thực

    content = await file.read()
    file_size = len(content)

    return await AttachmentService.create(
        db=db,
        message_id=message_id,
        file_name=file.filename,
        file_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        file_url=file_url,
    )


@router.get(
    "/messages/{message_id}/attachments",
    response_model=list[AttachmentResponse],
    summary="Danh sách attachments của message",
)
async def list_attachments(
    message_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        await MessageService.get_by_id(db, message_id)
    except NotFoundException as exc:
        _handle_service_error(exc)

    return await AttachmentService.list_by_message(db, message_id)


@router.delete(
    "/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa attachment",
)
async def delete_attachment(
    attachment_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        await AttachmentService.delete(db, attachment_id)
    except NotFoundException as exc:
        _handle_service_error(exc)


# ─────────────────────────────────────────────────────────────────────
# SSE helper
# ─────────────────────────────────────────────────────────────────────

def _sse(payload: dict) -> str:
    """Format payload thành SSE line."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"