from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.auth.models import User
from app.core.deps import SessionDep, SettingsDep
from app.core.security import decode_access_token

ACCESS_COOKIE = "mg_access"
REFRESH_COOKIE = "mg_refresh"

_UNAUTHENTICATED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Not signed in or session expired"
)


async def get_current_user(request: Request, session: SessionDep, settings: SettingsDep) -> User:
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise _UNAUTHENTICATED
    user_id = decode_access_token(token, settings.jwt_secret.get_secret_value())
    if user_id is None:
        raise _UNAUTHENTICATED
    user = await session.get(User, user_id)
    if user is None:
        raise _UNAUTHENTICATED
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
