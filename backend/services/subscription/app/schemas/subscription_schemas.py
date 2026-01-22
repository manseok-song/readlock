from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class PlanFeature(BaseModel):
    id: str
    name: str
    description: str
    included: bool


class PlanResponse(BaseModel):
    id: str
    name: str
    description: str
    price_monthly: float
    price_yearly: float
    currency: str = "KRW"
    features: List[PlanFeature]
    is_popular: bool = False
    trial_days: int = 0


class SubscriptionResponse(BaseModel):
    id: Optional[str] = None
    plan: Optional[PlanResponse] = None
    status: str  # active, cancelled, past_due, none
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    trial_end: Optional[datetime] = None


class SubscriptionCreateRequest(BaseModel):
    plan_id: str
    payment_method_id: Optional[str] = None
    billing_cycle: str = "monthly"  # monthly, yearly


class PaymentMethodResponse(BaseModel):
    id: str
    type: str  # card, bank_transfer, apple_pay, google_pay
    last4: Optional[str] = None
    brand: Optional[str] = None
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None
    is_default: bool = False
    created_at: datetime


class PaymentMethodCreateRequest(BaseModel):
    payment_token: str
    set_default: bool = True


class PaymentHistoryResponse(BaseModel):
    id: str
    amount: float
    currency: str
    status: str  # succeeded, pending, failed, refunded
    description: str
    payment_method: Optional[str] = None
    invoice_url: Optional[str] = None
    created_at: datetime


class CoinPurchaseRequest(BaseModel):
    package_id: str
    payment_method_id: Optional[str] = None


class CoinPackageResponse(BaseModel):
    id: str
    name: str
    coins: int
    bonus_coins: int
    price: float
    currency: str = "KRW"
    is_best_value: bool = False
