"""SQLAlchemy models. Importing this package registers every table on
`Base.metadata` (used by Alembic autogenerate)."""

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.trip import Trip
from app.models.user import User

__all__ = ["Conversation", "Message", "Trip", "User"]
