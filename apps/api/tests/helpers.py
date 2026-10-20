from typing import Any

from httpx import AsyncClient, Response

DEFAULT_CONSENTS: dict[str, bool] = {"core": True}


async def start_anonymous(
    client: AsyncClient, consents: dict[str, bool] | None = None, locale: str = "en"
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/auth/anonymous",
        json={"age_confirmed": True, "locale": locale, "consents": consents or DEFAULT_CONSENTS},
    )
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


async def register(
    client: AsyncClient, email: str = "asha@example.in", password: str = "correct horse battery"
) -> Response:
    return await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "age_confirmed": True,
            "consents": DEFAULT_CONSENTS,
        },
    )
