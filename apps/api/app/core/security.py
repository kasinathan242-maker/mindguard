import hashlib
import secrets
import uuid
from datetime import datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.db.types import utcnow

_hasher = PasswordHasher()  # argon2id with the library's current recommended parameters

# Verified against when an email is unknown, so a failed login costs the same either way.
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(16))

_JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def create_access_token(user_id: uuid.UUID, secret: str, ttl: timedelta) -> str:
    now = utcnow()
    claims = {"sub": str(user_id), "typ": "access", "iat": now, "exp": now + ttl}
    return jwt.encode(claims, secret, algorithm=_JWT_ALGORITHM)


def decode_access_token(token: str, secret: str) -> uuid.UUID | None:
    try:
        claims = jwt.decode(
            token, secret, algorithms=[_JWT_ALGORITHM], options={"require": ["sub", "exp"]}
        )
    except jwt.PyJWTError:
        return None
    if claims.get("typ") != "access":
        return None
    try:
        return uuid.UUID(str(claims["sub"]))
    except ValueError:
        return None


def new_refresh_token() -> tuple[str, str]:
    """Return (raw token for the cookie, SHA-256 digest for storage)."""
    raw = secrets.token_urlsafe(32)
    return raw, hash_refresh_token(raw)


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def expires_in(ttl: timedelta) -> datetime:
    return utcnow() + ttl
