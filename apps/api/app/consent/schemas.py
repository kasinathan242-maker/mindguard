from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator

ConsentScope = Literal["core", "chat_history", "voice", "wearables", "cloud_llm", "reminders"]

ALL_SCOPES: tuple[ConsentScope, ...] = (
    "core",
    "chat_history",
    "voice",
    "wearables",
    "cloud_llm",
    "reminders",
)

# Bump when the plain-language consent text changes; clients re-prompt on a mismatch.
CONSENT_VERSION = "1"


class InitialConsents(BaseModel):
    """Consents chosen at sign-up. `core` must be granted; everything else defaults off."""

    core: Literal[True]
    chat_history: bool = False
    voice: bool = False
    wearables: bool = False
    cloud_llm: bool = False
    reminders: bool = False

    def as_dict(self) -> dict[ConsentScope, bool]:
        return {scope: getattr(self, scope) for scope in ALL_SCOPES}


class ConsentUpdate(BaseModel):
    consents: dict[ConsentScope, bool]

    @field_validator("consents")
    @classmethod
    def _core_cannot_be_revoked(cls, value: dict[ConsentScope, bool]) -> dict[ConsentScope, bool]:
        if value.get("core") is False:
            raise ValueError(
                "core consent is required to use MindGuard; delete your account from the "
                "Privacy page instead"
            )
        return value


class ConsentOut(BaseModel):
    scope: ConsentScope
    granted: bool
    required: bool
    version: str | None
    granted_at: datetime | None
    revoked_at: datetime | None


class ConsentsResponse(BaseModel):
    current_version: str
    items: list[ConsentOut]
