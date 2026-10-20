from fastapi import APIRouter, Response

from app.safety.resources import Locale, ResourceOut, localised_resources

router = APIRouter(prefix="/safety", tags=["safety"])


@router.get("/resources")
async def get_resources(response: Response, locale: Locale = "en") -> list[ResourceOut]:
    """Public on purpose: crisis numbers must be reachable without a session."""
    response.headers["Cache-Control"] = "public, max-age=3600"
    return localised_resources(locale)
