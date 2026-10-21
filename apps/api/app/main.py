from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import health
from app.assessments.router import router as assessments_router
from app.auth.router import router as auth_router
from app.chat.router import default_provider
from app.chat.router import router as chat_router
from app.checkins.router import router as checkins_router
from app.consent.router import router as consent_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.core.resources import ResourcesFactory, default_resources
from app.emotion.service import load_optional_emotion_model
from app.integrations.wearables import router as wearables_router
from app.privacy.router import router as privacy_router
from app.reports.router import router as reports_router
from app.safety import engine as safety_engine
from app.safety.router import router as safety_router

API_PREFIX = "/api/v1"


def create_app(
    settings: Settings | None = None,
    resources_factory: ResourcesFactory = default_resources,
) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        safety_engine.configure(settings.safety_classifier)
        app.state.emotion_model = load_optional_emotion_model(settings.emotion_enabled)
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
    app.state.provider_factory = default_provider
    app.state.emotion_model = None

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
    api.include_router(assessments_router)
    api.include_router(safety_router)
    api.include_router(chat_router)
    api.include_router(checkins_router)
    api.include_router(privacy_router)
    api.include_router(reports_router)
    api.include_router(wearables_router)
    app.include_router(api)
    return app
