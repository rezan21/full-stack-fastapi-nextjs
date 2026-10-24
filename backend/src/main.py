import logging
from typing import Any

import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from src.agent import contract as agent_contract
from src.agent import runtime as agent_runtime
from src.auth import router as auth_router
from src.chat import router as chat_router
from src.config import settings
from src.health import router as health_router
from src.items import router as items_router
from src.users import router as users_router
from src.utils import event_scrubber

logging.basicConfig(level=logging.INFO)


def custom_generate_unique_id(route: APIRoute) -> str:
    """Build the operation id for a route."""
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.FASTAPI_ENV != "development":
    sentry_sdk.init(
        dsn=str(settings.SENTRY_DSN),
        enable_tracing=True,
        event_scrubber=event_scrubber(),
    )


class API(FastAPI):
    """FastAPI app whose OpenAPI spec also carries the models the agent's tools answer with."""

    def openapi(self) -> dict[str, Any]:
        spec = super().openapi()
        spec["components"]["schemas"].update(agent_contract.contract_schemas())
        return spec


def build_app(*, docs: bool) -> FastAPI:
    """Build the API, serving its interactive docs only when asked."""
    app = API(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if docs else None,
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        generate_unique_id_function=custom_generate_unique_id,
        lifespan=agent_runtime.lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_HOST],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in (
        auth_router.router,
        users_router.router,
        health_router.router,
        items_router.router,
        chat_router.router,
    ):
        app.include_router(router, prefix=settings.API_V1_STR)
    return app


app = build_app(docs=settings.FASTAPI_ENV == "development")
