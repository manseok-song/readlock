from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.core.config import settings
from .api import router

app = FastAPI(
    title="ReadLock Gamification Service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
    return {"status": "healthy", "service": "gamification"}
