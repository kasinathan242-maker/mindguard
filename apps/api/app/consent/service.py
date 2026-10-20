import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record
from app.consent.models import Consent
from app.consent.schemas import (
    ALL_SCOPES,
    CONSENT_VERSION,
    ConsentOut,
    ConsentScope,
    ConsentsResponse,
)
from app.db.types import utcnow


async def _rows(session: AsyncSession, user_id: uuid.UUID) -> dict[str, Consent]:
    result = await session.scalars(select(Consent).where(Consent.user_id == user_id))
    return {row.scope: row for row in result}


async def apply_consents(
    session: AsyncSession, user_id: uuid.UUID, changes: dict[ConsentScope, bool]
) -> None:
    """Stage consent changes and their audit entries. Unchanged scopes are left untouched."""
    rows = await _rows(session, user_id)
    now = utcnow()
    for scope, granted in changes.items():
        row = rows.get(scope)
        if row is None:
            row = Consent(user_id=user_id, scope=scope, granted=False, version=CONSENT_VERSION)
            session.add(row)
            rows[scope] = row
            if not granted:
                continue  # left off from the start: stored as a choice, not a revocation
        elif row.granted == granted:
            continue
        row.granted = granted
        if granted:
            row.version = CONSENT_VERSION
            row.granted_at = now
            row.revoked_at = None
            record(session, user_id, f"consent.grant.{scope}")
        else:
            row.revoked_at = now
            record(session, user_id, f"consent.revoke.{scope}")
            await _erase_scope_data(session, user_id, scope)


async def _erase_scope_data(session: AsyncSession, user_id: uuid.UUID, scope: str) -> None:
    """Withdrawing consent also removes the data that consent covered."""
    if scope == "wearables":
        from app.integrations.wearables import WearableSample  # avoids an import cycle

        await session.execute(delete(WearableSample).where(WearableSample.user_id == user_id))


async def list_consents(session: AsyncSession, user_id: uuid.UUID) -> ConsentsResponse:
    rows = await _rows(session, user_id)
    items = []
    for scope in ALL_SCOPES:
        row = rows.get(scope)
        items.append(
            ConsentOut(
                scope=scope,
                granted=bool(row and row.granted),
                required=scope == "core",
                version=row.version if row else None,
                granted_at=row.granted_at if row else None,
                revoked_at=row.revoked_at if row else None,
            )
        )
    return ConsentsResponse(current_version=CONSENT_VERSION, items=items)


async def has_consent(session: AsyncSession, user_id: uuid.UUID, scope: ConsentScope) -> bool:
    granted = await session.scalar(
        select(Consent.granted).where(Consent.user_id == user_id, Consent.scope == scope)
    )
    return bool(granted)
