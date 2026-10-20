import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, EmailStr, Field

from app.consent.schemas import InitialConsents

Locale = Literal["en", "ta"]


def _normalise_email(value: str) -> str:
    return value.strip().lower()


Email = Annotated[EmailStr, AfterValidator(_normalise_email)]
# 10+ characters, no composition rules (NIST SP 800-63B); argon2 input capped to bound cost.
Password = Annotated[str, Field(min_length=10, max_length=128)]


class AnonymousStart(BaseModel):
    age_confirmed: Literal[True]
    locale: Locale = "en"
    consents: InitialConsents


class Register(BaseModel):
    email: Email
    password: Password
    age_confirmed: Literal[True]
    locale: Locale = "en"
    consents: InitialConsents


class Login(BaseModel):
    email: Email
    password: Annotated[str, Field(min_length=1, max_length=128)]


class Upgrade(BaseModel):
    email: Email
    password: Password


class LocaleUpdate(BaseModel):
    locale: Locale


class UserOut(BaseModel):
    id: uuid.UUID
    is_anonymous: bool
    email: str | None
    locale: Locale
    created_at: datetime
