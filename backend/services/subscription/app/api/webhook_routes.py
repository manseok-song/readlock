from fastapi import APIRouter, Request, HTTPException, Header
import hmac
import hashlib

from shared.core.config import settings
from ..services.webhook_service import WebhookService

router = APIRouter()


def get_webhook_service() -> WebhookService:
    return WebhookService()


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
):
    """Handle Stripe webhook events"""
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    payload = await request.body()

    service = get_webhook_service()
    result = await service.handle_stripe_webhook(
        payload=payload,
        signature=stripe_signature,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"received": True}


@router.post("/apple")
async def apple_webhook(
    request: Request,
):
    """Handle Apple App Store webhook events"""
    payload = await request.json()

    service = get_webhook_service()
    result = await service.handle_apple_webhook(payload=payload)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"received": True}


@router.post("/google")
async def google_webhook(
    request: Request,
):
    """Handle Google Play webhook events"""
    payload = await request.json()

    service = get_webhook_service()
    result = await service.handle_google_webhook(payload=payload)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"received": True}
