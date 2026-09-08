from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List
from uuid import UUID
from fastapi import HTTPException
import math

from app.modules.chat_core.models import Conversation, Message, Attachment, RoleEnum
from app.modules.chat_core.schemas import (
    ConversationCreate,
    ConversationUpdate,
    MessageCreate,
    MessageUpdate,
    ChatRequest,
    PaginatedConversations,
    PaginatedMessages,
)


# ═══════════════════════════════════════════════════════════
# CONVERSATION SERVICE
# ═══════════════════════════════════════════════════════════

class ConversationService:

    # ── Create ─────────────────────────────────────────────

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: UUID,
        payload: ConversationCreate,
    ) -> Conversation:
        conversation = Conversation(
            user_id=user_id,
            model_id=payload.model_id,
            folder_id=payload.folder_id,
            title=payload.title,
            system_prompt=payload.system_prompt,
            temperature=payload.temperature,
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation

    # ── Read one ───────────────────────────────────────────

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Conversation:
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        return conversation

    # ── Read with messages ─────────────────────────────────

    @staticmethod
    async def get_with_messages(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Conversation:
        result = await db.execute(
            select(Conversation)
            .options(
                selectinload(Conversation.messages).selectinload(Message.attachments)
            )
            .where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
        if conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        return conversation

    # ── List (paginated) ───────────────────────────────────

    @staticmethod
    async def list_by_user(
        db: AsyncSession,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        is_archived: Optional[bool] = False,
        folder_id: Optional[UUID] = None,
    ) -> PaginatedConversations:
        base_query = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .where(Conversation.is_archived == is_archived)
        )

        if folder_id is not None:
            base_query = base_query.where(Conversation.folder_id == folder_id)

        # total count
        count_result = await db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar_one()

        # paginated items — pinned first, then by updated_at desc
        items_result = await db.execute(
            base_query
            .order_by(Conversation.is_pinned.desc(), Conversation.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = items_result.scalars().all()

        return PaginatedConversations(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total else 1,
        )

    # ── Update ─────────────────────────────────────────────

    @staticmethod
    async def update(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: UUID,
        payload: ConversationUpdate,
    ) -> Conversation:
        conversation = await ConversationService.get_by_id(db, conversation_id, user_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(conversation, field, value)

        await db.commit()
        await db.refresh(conversation)
        return conversation

    # ── Archive / Pin toggles ──────────────────────────────

    @staticmethod
    async def toggle_archive(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Conversation:
        conversation = await ConversationService.get_by_id(db, conversation_id, user_id)
        conversation.is_archived = not conversation.is_archived
        await db.commit()
        await db.refresh(conversation)
        return conversation

    @staticmethod
    async def toggle_pin(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Conversation:
        conversation = await ConversationService.get_by_id(db, conversation_id, user_id)
        conversation.is_pinned = not conversation.is_pinned
        await db.commit()
        await db.refresh(conversation)
        return conversation

    # ── Delete ─────────────────────────────────────────────

    @staticmethod
    async def delete(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: UUID,
    ) -> None:
        conversation = await ConversationService.get_by_id(db, conversation_id, user_id)
        await db.delete(conversation)
        await db.commit()


# ═══════════════════════════════════════════════════════════
# MESSAGE SERVICE
# ═══════════════════════════════════════════════════════════

class MessageService:

    # ── Create ─────────────────────────────────────────────

    @staticmethod
    async def create(
        db: AsyncSession,
        payload: MessageCreate,
        token_count: int = 0,
        finish_reason: Optional[str] = None,
    ) -> Message:
        message = Message(
            conversation_id=payload.conversation_id,
            parent_message_id=payload.parent_message_id,
            role=payload.role,
            content=payload.content,
            model_id=payload.model_id,
            metadata=payload.metadata,
            token_count=token_count,
            finish_reason=finish_reason,
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message

    # ── Read ───────────────────────────────────────────────

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        message_id: UUID,
    ) -> Message:
        result = await db.execute(
            select(Message)
            .options(selectinload(Message.attachments))
            .where(Message.id == message_id)
        )
        message = result.scalar_one_or_none()
        if not message:
            raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
        return message

    # ── List by conversation (paginated) ───────────────────

    @staticmethod
    async def list_by_conversation(
        db: AsyncSession,
        conversation_id: UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedMessages:
        base_query = (
            select(Message)
            .options(selectinload(Message.attachments))
            .where(Message.conversation_id == conversation_id)
        )

        count_result = await db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar_one()

        items_result = await db.execute(
            base_query
            .order_by(Message.created_at.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = items_result.scalars().all()

        return PaginatedMessages(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total else 1,
        )

    # ── Get thread (walk parent chain) ────────────────────

    @staticmethod
    async def get_thread(
        db: AsyncSession,
        message_id: UUID,
    ) -> List[Message]:
        """Trả về chuỗi message từ root → message hiện tại (dùng cho branching)."""
        thread: List[Message] = []
        current_id: Optional[UUID] = message_id

        while current_id:
            result = await db.execute(
                select(Message)
                .options(selectinload(Message.attachments))
                .where(Message.id == current_id)
            )
            msg = result.scalar_one_or_none()
            if not msg:
                break
            thread.insert(0, msg)
            current_id = msg.parent_message_id

        return thread

    # ── Update ─────────────────────────────────────────────

    @staticmethod
    async def update(
        db: AsyncSession,
        message_id: UUID,
        payload: MessageUpdate,
    ) -> Message:
        message = await MessageService.get_by_id(db, message_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(message, field, value)
        await db.commit()
        await db.refresh(message)
        return message

    # ── Delete ─────────────────────────────────────────────

    @staticmethod
    async def delete(
        db: AsyncSession,
        message_id: UUID,
    ) -> None:
        message = await MessageService.get_by_id(db, message_id)
        await db.delete(message)
        await db.commit()


# ═══════════════════════════════════════════════════════════
# ATTACHMENT SERVICE
# ═══════════════════════════════════════════════════════════

class AttachmentService:

    @staticmethod
    async def create(
        db: AsyncSession,
        message_id: UUID,
        file_name: str,
        file_type: str,
        file_size: int,
        file_url: str,
    ) -> Attachment:
        attachment = Attachment(
            message_id=message_id,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            file_url=file_url,
        )
        db.add(attachment)
        await db.commit()
        await db.refresh(attachment)
        return attachment

    @staticmethod
    async def list_by_message(
        db: AsyncSession,
        message_id: UUID,
    ) -> List[Attachment]:
        result = await db.execute(
            select(Attachment).where(Attachment.message_id == message_id)
        )
        return result.scalars().all()

    @staticmethod
    async def delete(
        db: AsyncSession,
        attachment_id: UUID,
    ) -> None:
        result = await db.execute(
            select(Attachment).where(Attachment.id == attachment_id)
        )
        attachment = result.scalar_one_or_none()
        if not attachment:
            raise HTTPException(status_code=404, detail=f"Attachment {attachment_id} not found")
        await db.delete(attachment)
        await db.commit()


# ═══════════════════════════════════════════════════════════
# CHAT ORCHESTRATION SERVICE
# ═══════════════════════════════════════════════════════════

class ChatService:
    """
    Orchestrate: tạo conversation + ghi user message + placeholder assistant message.
    Phần gọi LLM thực tế sẽ được inject từ tầng router/websocket.
    """

    @staticmethod
    async def start_chat(
        db: AsyncSession,
        user_id: UUID,
        payload: ChatRequest,
    ) -> tuple[Conversation, Message]:
        """
        Tạo conversation mới và lưu user message đầu tiên.
        Trả về (conversation, user_message) để router tiếp tục gọi LLM.
        """
        # 1. Tạo conversation
        conversation = await ConversationService.create(
            db=db,
            user_id=user_id,
            payload=ConversationCreate(
                model_id=payload.model_id,
                folder_id=payload.folder_id,
                title=payload.title or payload.message[:80],
                system_prompt=payload.system_prompt,
                temperature=payload.temperature,
            ),
        )

        # 2. Lưu user message
        user_message = await MessageService.create(
            db=db,
            payload=MessageCreate(
                conversation_id=conversation.id,
                role=RoleEnum.user,
                content=payload.message,
                model_id=payload.model_id,
            ),
        )

        return conversation, user_message

    @staticmethod
    async def send_message(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: UUID,
        content: str,
        parent_message_id: Optional[UUID] = None,
        metadata: Optional[dict] = None,
    ) -> Message:
        """
        Gửi tiếp message vào conversation đã có.
        Trả về user_message; assistant reply do router xử lý sau.
        """
        # Verify ownership
        conversation = await ConversationService.get_by_id(db, conversation_id, user_id)

        user_message = await MessageService.create(
            db=db,
            payload=MessageCreate(
                conversation_id=conversation.id,
                role=RoleEnum.user,
                content=content,
                model_id=conversation.model_id,
                parent_message_id=parent_message_id,
                metadata=metadata,
            ),
        )

        return user_message

    @staticmethod
    async def save_assistant_reply(
        db: AsyncSession,
        conversation_id: UUID,
        content: str,
        model_id: UUID,
        parent_message_id: Optional[UUID] = None,
        token_count: int = 0,
        finish_reason: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Message:
        """Lưu câu trả lời từ LLM vào DB sau khi stream hoàn thành."""
        assistant_message = await MessageService.create(
            db=db,
            payload=MessageCreate(
                conversation_id=conversation_id,
                role=RoleEnum.assistant,
                content=content,
                model_id=model_id,
                parent_message_id=parent_message_id,
                metadata=metadata,
            ),
            token_count=token_count,
            finish_reason=finish_reason,
        )
        return assistant_message