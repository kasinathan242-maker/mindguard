from fastapi import APIRouter

from app.auth.deps import CurrentUser
from app.consent.schemas import ConsentsResponse, ConsentUpdate
from app.consent.service import apply_consents, list_consents
from app.core.deps import SessionDep

router = APIRouter(prefix="/consents", tags=["consent"])


@router.get("")
async def get_consents(user: CurrentUser, session: SessionDep) -> ConsentsResponse:
    return await list_consents(session, user.id)


@router.put("")
async def put_consents(
    body: ConsentUpdate, user: CurrentUser, session: SessionDep
) -> ConsentsResponse:
    await apply_consents(session, user.id, body.consents)
    await session.commit()
    return await list_consents(session, user.id)
