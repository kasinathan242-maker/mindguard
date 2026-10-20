from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from app.auth import service
from app.auth.deps import ACCESS_COOKIE, REFRESH_COOKIE, CurrentUser
from app.auth.models import User
from app.auth.schemas import AnonymousStart, LocaleUpdate, Login, Register, Upgrade, UserOut
from app.core.config import Settings
from app.core.deps import SessionDep, SettingsDep
from app.core.rate_limit import rate_limit

REFRESH_COOKIE_PATH = "/api/v1/auth"


def _auth_limit(request: Request) -> int:
    settings: Settings = request.app.state.settings
    return settings.auth_rate_limit_per_minute


router = APIRouter(prefix="/auth", tags=["auth"])

# Applied to endpoints that create sessions or accept credentials; /me stays unthrottled.
AuthRateLimit = [Depends(rate_limit("auth", _auth_limit))]


def _set_session_cookies(
    response: Response, tokens: service.IssuedTokens, settings: Settings
) -> None:
    response.set_cookie(
        ACCESS_COOKIE,
        tokens.access,
        max_age=settings.access_token_ttl_minutes * 60,
        path="/api",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
    )
    response.set_cookie(
        REFRESH_COOKIE,
        tokens.refresh,
        max_age=settings.refresh_token_ttl_days * 86_400,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
    )


def _clear_session_cookies(response: Response, settings: Settings) -> None:
    for name, path in ((ACCESS_COOKIE, "/api"), (REFRESH_COOKIE, REFRESH_COOKIE_PATH)):
        response.delete_cookie(
            name, path=path, httponly=True, secure=settings.cookie_secure, samesite="strict"
        )


def _out(user: User) -> UserOut:
    return UserOut.model_validate(user, from_attributes=True)


_EMAIL_TAKEN = HTTPException(
    status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists"
)


@router.post("/anonymous", status_code=status.HTTP_201_CREATED, dependencies=AuthRateLimit)
async def start_anonymous(
    body: AnonymousStart, response: Response, session: SessionDep, settings: SettingsDep
) -> UserOut:
    user, tokens = await service.start_anonymous(
        session, settings, locale=body.locale, consents=body.consents
    )
    _set_session_cookies(response, tokens, settings)
    return _out(user)


@router.post("/register", status_code=status.HTTP_201_CREATED, dependencies=AuthRateLimit)
async def register(
    body: Register, response: Response, session: SessionDep, settings: SettingsDep
) -> UserOut:
    try:
        user, tokens = await service.register(
            session,
            settings,
            email=body.email,
            password=body.password,
            locale=body.locale,
            consents=body.consents,
        )
    except service.EmailTakenError:
        raise _EMAIL_TAKEN from None
    _set_session_cookies(response, tokens, settings)
    return _out(user)


@router.post("/login", dependencies=AuthRateLimit)
async def login(
    body: Login, response: Response, session: SessionDep, settings: SettingsDep
) -> UserOut:
    try:
        user, tokens = await service.login(
            session, settings, email=body.email, password=body.password
        )
    except service.InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email or password is incorrect"
        ) from None
    _set_session_cookies(response, tokens, settings)
    return _out(user)


@router.post("/upgrade", dependencies=AuthRateLimit)
async def upgrade(body: Upgrade, user: CurrentUser, session: SessionDep) -> UserOut:
    try:
        upgraded = await service.upgrade(session, user, email=body.email, password=body.password)
    except service.AlreadyUpgradedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This account already has an email"
        ) from None
    except service.EmailTakenError:
        raise _EMAIL_TAKEN from None
    return _out(upgraded)


@router.post("/refresh", response_model=UserOut, dependencies=AuthRateLimit)
async def refresh(
    response: Response,
    session: SessionDep,
    settings: SettingsDep,
    mg_refresh: Annotated[str | None, Cookie()] = None,
) -> UserOut | JSONResponse:
    try:
        if not mg_refresh:
            raise service.InvalidRefreshTokenError
        user, tokens = await service.rotate(session, settings, mg_refresh)
    except service.InvalidRefreshTokenError:
        expired = JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Session expired"}
        )
        _clear_session_cookies(expired, settings)
        return expired
    _set_session_cookies(response, tokens, settings)
    return _out(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    session: SessionDep,
    settings: SettingsDep,
    mg_refresh: Annotated[str | None, Cookie()] = None,
) -> None:
    await service.logout(session, mg_refresh)
    _clear_session_cookies(response, settings)


@router.get("/me")
async def me(user: CurrentUser) -> UserOut:
    return _out(user)


@router.put("/me/locale")
async def set_locale(body: LocaleUpdate, user: CurrentUser, session: SessionDep) -> UserOut:
    user.locale = body.locale
    await session.commit()
    return _out(user)
