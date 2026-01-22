from fastapi import APIRouter
from .subscription_routes import router as subscription_router
from .payment_routes import router as payment_router
from .webhook_routes import router as webhook_router

router = APIRouter()
router.include_router(subscription_router, prefix="/subscriptions", tags=["subscriptions"])
router.include_router(payment_router, prefix="/payments", tags=["payments"])
router.include_router(webhook_router, prefix="/webhooks", tags=["webhooks"])
