import uuid
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record
from app.auth.models import RefreshToken, User
from app.consent.schemas import InitialConsents
from app.consent.service import apply_consents
from app.core.config import Settings
from app.core.security import (
    create_access_token,
    expires_in,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    password_needs_rehash,
    verify_password,
)
from app.db.types import utcnow


class EmailTakenError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InvalidRefreshTokenError(Exception):
    pass


class AlreadyUpgradedError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class IssuedTokens:
    access: str
    refresh: str


async def _issue(
    session: AsyncSession, user: User, settings: Settings, family_id: uuid.UUID | None = None
) -> IssuedTokens:
    raw, digest = new_refresh_token()
    session.add(
        RefreshToken(
            user_id=user.id,
            family_id=family_id or uuid.uuid4(),
            token_hash=digest,
            expires_at=expires_in(timedelta(days=settings.refresh_token_ttl_days)),
        )
    )
    access = create_access_token(
        user.id,
        settings.jwt_secret.get_secret_value(),
        timedelta(minutes=settings.access_token_ttl_minutes),
    )
    return IssuedTokens(access=access, refresh=raw)


async def _create_user(
    session: AsyncSession,
    *,
    locale: str,
    consents: InitialConsents,
    email: str | None = None,
    password: str | None = None,
) -> User:
    user = User(
        is_anonymous=email is None,
        email=email,
        password_hash=hash_password(password) if password else None,
        locale=locale,
    )
    session.add(user)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise EmailTakenError from exc
    await apply_consents(session, user.id, consents.as_dict())
    return user


async def start_anonymous(
    session: AsyncSession, settings: Settings, *, locale: str, consents: InitialConsents
) -> tuple[User, IssuedTokens]:
    user = await _create_user(session, locale=locale, consents=consents)
    tokens = await _issue(session, user, settings)
    await session.commit()
    return user, tokens


async def register(
    session: AsyncSession,
    settings: Settings,
    *,
    email: str,
    password: str,
    locale: str,
    consents: InitialConsents,
) -> tuple[User, IssuedTokens]:
    if await session.scalar(select(User.id).where(User.email == email)):
        raise EmailTakenError
    user = await _create_user(
        session, locale=locale, consents=consents, email=email, password=password
    )
    tokens = await _issue(session, user, settings)
    await session.commit()
    return user, tokens


async def login(
    session: AsyncSession, settings: Settings, *, email: str, password: str
) -> tuple[User, IssuedTokens]:
    user = await session.scalar(select(User).where(User.email == email))
    if not verify_password(user.password_hash if user else None, password) or user is None:
        raise InvalidCredentialsError
    if user.password_hash and password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    tokens = await _issue(session, user, settings)
    await session.commit()
    return user, tokens


async def upgrade(session: AsyncSession, user: User, *, email: str, password: str) -> User:
    """Attach credentials to an anonymous account. Rows keep their user_id, so no data moves."""
    if not user.is_anonymous:
        raise AlreadyUpgradedError
    if await session.scalar(select(User.id).where(User.email == email)):
        raise EmailTakenError
    user.email = email
    user.password_hash = hash_password(password)
    user.is_anonymous = False
    record(session, user.id, "account.upgrade")
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise EmailTakenError from exc
    return user


async def rotate(session: AsyncSession, settings: Settings, raw: str) -> tuple[User, IssuedTokens]:
    token = await session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw))
    )
    if token is None:
        raise InvalidRefreshTokenError
    now = utcnow()
    if token.revoked_at is not None:
        # A rotated token came back: assume theft and end every session in its family.
        await session.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == token.family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await session.commit()
        raise InvalidRefreshTokenError
    if token.expires_at <= now:
        raise InvalidRefreshTokenError
    user = await session.get(User, token.user_id)
    if user is None:
        raise InvalidRefreshTokenError
    token.revoked_at = now
    tokens = await _issue(session, user, settings, family_id=token.family_id)
    await session.commit()
    return user, tokens


async def logout(session: AsyncSession, raw: str | None) -> None:
    if not raw:
        return
    await session.execute(
        update(RefreshToken)
        .where(
            RefreshToken.token_hash == hash_refresh_token(raw), RefreshToken.revoked_at.is_(None)
        )
        .values(revoked_at=utcnow())
    )
    await session.commit()
