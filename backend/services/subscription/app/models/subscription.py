from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Float, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from shared.core.database import Base


class Plan(Base):
    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    price_monthly = Column(Float, nullable=False)
    price_yearly = Column(Float, nullable=False)
    currency = Column(String(3), default="KRW")
    features = Column(JSON, nullable=False)
    is_popular = Column(Boolean, default=False)
    trial_days = Column(Integer, default=0)
    stripe_price_monthly_id = Column(String(100), nullable=True)
    stripe_price_yearly_id = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price_monthly": self.price_monthly,
            "price_yearly": self.price_yearly,
            "currency": self.currency,
            "features": self.features,
            "is_popular": self.is_popular,
            "trial_days": self.trial_days,
        }


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False)
    status = Column(String(20), nullable=False)  # active, cancelled, past_due, trialing
    billing_cycle = Column(String(10), default="monthly")
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    cancel_at_period_end = Column(Boolean, default=False)
    cancelled_at = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    stripe_subscription_id = Column(String(100), nullable=True)
    stripe_customer_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(20), nullable=False)  # card, bank_transfer, apple_pay, google_pay
    stripe_payment_method_id = Column(String(100), nullable=True)
    last4 = Column(String(4), nullable=True)
    brand = Column(String(20), nullable=True)
    exp_month = Column(Integer, nullable=True)
    exp_year = Column(Integer, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "last4": self.last4,
            "brand": self.brand,
            "exp_month": self.exp_month,
            "exp_year": self.exp_year,
            "is_default": self.is_default,
            "created_at": self.created_at,
        }


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="KRW")
    status = Column(String(20), nullable=False)  # succeeded, pending, failed, refunded
    description = Column(String(200), nullable=True)
    payment_method_id = Column(UUID(as_uuid=True), nullable=True)
    stripe_payment_intent_id = Column(String(100), nullable=True)
    stripe_invoice_id = Column(String(100), nullable=True)
    invoice_url = Column(String(500), nullable=True)
    payment_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "description": self.description,
            "payment_method": self.payment_method_id,
            "invoice_url": self.invoice_url,
            "created_at": self.created_at,
        }


class CoinPackage(Base):
    __tablename__ = "coin_packages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    coins = Column(Integer, nullable=False)
    bonus_coins = Column(Integer, default=0)
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="KRW")
    is_best_value = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    stripe_price_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "coins": self.coins,
            "bonus_coins": self.bonus_coins,
            "price": self.price,
            "currency": self.currency,
            "is_best_value": self.is_best_value,
        }
