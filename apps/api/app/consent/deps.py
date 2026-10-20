from collections.abc import Awaitable, Callable

from fastapi import HTTPException, status

from app.auth.deps import CurrentUser
from app.auth.models import User
from app.consent.schemas import ConsentScope
from app.consent.service import has_consent
from app.core.deps import SessionDep


def require_consent(scope: ConsentScope) -> Callable[[CurrentUser, SessionDep], Awaitable[User]]:
    """Dependency that returns the current user only if they have granted `scope`."""

    async def dependency(user: CurrentUser, session: SessionDep) -> User:
        if not await has_consent(session, user.id, scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "consent_required", "scope": scope},
            )
        return user

    return dependency
