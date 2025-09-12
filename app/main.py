"""FastAPI application main module."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router
from app.config.settings import SETTINGS
from app.utils.database import close_db_connections, open_db_connections


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    try:
        # Startup
        print(f"Starting {SETTINGS.app_name}. debug={SETTINGS.app_debug}")
        await open_db_connections()
        print("Application startup completess")
        yield

    finally:
        # Shutdown
        print("Shutting down application...")
        await close_db_connections()
        print("Application shutdown complete")


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title=SETTINGS.app_name,
        version="0.0.1",
        description="WeMasterTrade ChatBot API",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    return app


# Create the application instance
app = create_application()
