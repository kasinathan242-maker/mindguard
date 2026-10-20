from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import health
from app.auth.router import router as auth_router
from app.consent.router import router as consent_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.core.resources import ResourcesFactory, default_resources

API_PREFIX = "/api/v1"


def create_app(
    settings: Settings | None = None,
    resources_factory: ResourcesFactory = default_resources,
) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        async with resources_factory(settings) as resources:
            app.state.resources = resources
            yield

    app = FastAPI(
        title="MindGuard AI API",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/api/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/api/openapi.json",
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
    )

    api = APIRouter(prefix=API_PREFIX)
    api.include_router(health.router)
    api.include_router(auth_router)
    api.include_router(consent_router)
    app.include_router(api)
    return app
