import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog


def record(session: AsyncSession, user_id: uuid.UUID | None, action: str) -> None:
    """Stage an audit entry in the caller's transaction, so it commits or rolls back with it."""
    session.add(AuditLog(user_id=user_id, action=action))
