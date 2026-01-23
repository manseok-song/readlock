from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.core.config import settings
from .api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Notification Service starting...")
    yield
    print("Notification Service shutting down...")


app = FastAPI(
    title="ReadLock Notification Service",
    description="Push notifications and in-app messaging",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.API_PREFIX)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "notification"}
