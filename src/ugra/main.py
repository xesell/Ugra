"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ugra.config.settings import get_settings
from ugra.core.di.container import Container, bootstrap_mcp
from ugra.core.logging.setup import setup_logging
from ugra.core.observability.metrics import setup_metrics
from ugra.core.observability.tracing import setup_tracing
from ugra.infrastructure.persistence.database import Base
from ugra.presentation.api.routes import router


def _resolve_user_id(settings, container: Container) -> UUID:
    if settings.default_user_id:
        return UUID(settings.default_user_id)
    return uuid4()


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = app.state.container
    settings = container.config()

    engine = container.db_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    bootstrap_mcp(container)
    container.event_handlers()  # wire event subscriptions

    user_id = _resolve_user_id(settings, container)

    if settings.autonomous_enabled:
        first_task = container.first_autonomous_task()
        await first_task.run(user_id)

        scheduler = container.autonomous_scheduler()
        await scheduler.start(user_id)

    yield

    if settings.autonomous_enabled:
        await container.autonomous_scheduler().stop()
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings)

    if not settings.debug:
        setup_tracing(settings)
        setup_metrics(settings)

    container = Container()
    container.wire()

    app = FastAPI(
        title="Ugra AI Workforce Platform",
        description="Personal AI agents for professional career development",
        version="0.2.0",
        lifespan=lifespan,
    )
    app.state.container = container

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix="/api/v1")
    return app


app = create_app()
