from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.core.config import settings
from shared.middleware.rate_limit import RateLimitMiddleware
from .api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    print("Map Service starting...")
    yield
    print("Map Service shutting down...")


app = FastAPI(
    title="ReadLock Map Service",
    description="Bookstore map and location-based features",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
    burst_size=settings.RATE_LIMIT_BURST,
)

# Routes
app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "map"}
