"""Security headers on every API response (nginx sets them too; this covers direct access)."""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response

HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Cache-Control": "no-store",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}
HSTS = "max-age=31536000; includeSubDomains"


def security_headers(
    hsts: bool,
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    async def middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        for name, value in HEADERS.items():
            # Endpoints that set their own caching (crisis resources) keep it.
            response.headers.setdefault(name, value)
        if hsts:
            response.headers["Strict-Transport-Security"] = HSTS
        return response

    return middleware
