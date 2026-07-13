"""Data access for conversations and their messages."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation, Message


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, trip_id: UUID, thread_id: UUID) -> Conversation:
        conversation = Conversation(trip_id=trip_id, thread_id=thread_id)
        self._session.add(conversation)
        await self._session.flush()
        return conversation

    async def get_by_trip(self, trip_id: UUID) -> Conversation | None:
        result = await self._session.execute(
            select(Conversation).where(Conversation.trip_id == trip_id)
        )
        return result.scalar_one_or_none()


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_trip(self, trip_id: UUID, *, limit: int, offset: int) -> list[Message]:
        result = await self._session.execute(
            select(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.trip_id == trip_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def add(
        self, *, conversation_id: UUID, role: str, content: str, agent_events: dict[str, Any] | None
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            agent_events=agent_events,
        )
        self._session.add(message)
        await self._session.flush()
        return message
