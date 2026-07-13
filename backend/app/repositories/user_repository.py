"""Data access for users."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_google_id(self, google_id: str) -> User | None:
        result = await self._session.execute(select(User).where(User.google_id == google_id))
        return result.scalar_one_or_none()

    async def create(self, *, email: str, hashed_password: str, name: str | None) -> User:
        user = User(email=email, hashed_password=hashed_password, name=name)
        self._session.add(user)
        await self._session.flush()
        return user

    async def create_google(self, *, email: str, google_id: str, name: str | None) -> User:
        """Create a Google-only account (no password)."""
        user = User(email=email, google_id=google_id, name=name)
        self._session.add(user)
        await self._session.flush()
        return user
