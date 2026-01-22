"""Create subscription tables

Revision ID: 009
Revises: 008
Create Date: 2024-01-01

Note: A simple subscriptions table already exists in 001_initial.
This migration adds the full subscription system with plans, payment methods, etc.
The existing subscriptions table will be modified to reference subscription_plans.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    # Subscription plans
    op.create_table(
        'subscription_plans',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('price_monthly', sa.Float(), nullable=False),
        sa.Column('price_yearly', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), server_default="'KRW'"),
        sa.Column('features', JSON, nullable=False),
        sa.Column('is_popular', sa.Boolean(), server_default='false'),
        sa.Column('trial_days', sa.Integer(), server_default='0'),
        sa.Column('stripe_price_monthly_id', sa.String(100), nullable=True),
        sa.Column('stripe_price_yearly_id', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # Modify existing subscriptions table to add missing columns
    op.add_column('subscriptions', sa.Column('plan_id', UUID(as_uuid=True), nullable=True))
    op.add_column('subscriptions', sa.Column('billing_cycle', sa.String(10), server_default="'monthly'"))
    op.add_column('subscriptions', sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('subscriptions', sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True))
    op.add_column('subscriptions', sa.Column('cancel_at_period_end', sa.Boolean(), server_default='false'))
    op.add_column('subscriptions', sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('subscriptions', sa.Column('trial_end', sa.DateTime(timezone=True), nullable=True))
    op.add_column('subscriptions', sa.Column('stripe_subscription_id', sa.String(100), nullable=True))
    op.add_column('subscriptions', sa.Column('stripe_customer_id', sa.String(100), nullable=True))
    op.create_index('ix_subscriptions_stripe_id', 'subscriptions', ['stripe_subscription_id'])

    # Payment methods
    op.create_table(
        'payment_methods',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('stripe_payment_method_id', sa.String(100), nullable=True),
        sa.Column('last4', sa.String(4), nullable=True),
        sa.Column('brand', sa.String(20), nullable=True),
        sa.Column('exp_month', sa.Integer(), nullable=True),
        sa.Column('exp_year', sa.Integer(), nullable=True),
        sa.Column('is_default', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_payment_methods_user_id', 'payment_methods', ['user_id'])

    # Payments
    op.create_table(
        'payments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subscription_id', UUID(as_uuid=True), sa.ForeignKey('subscriptions.id'), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), server_default="'KRW'"),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('description', sa.String(200), nullable=True),
        sa.Column('payment_method_id', UUID(as_uuid=True), nullable=True),
        sa.Column('stripe_payment_intent_id', sa.String(100), nullable=True),
        sa.Column('stripe_invoice_id', sa.String(100), nullable=True),
        sa.Column('invoice_url', sa.String(500), nullable=True),
        sa.Column('payment_metadata', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_payments_user_id', 'payments', ['user_id'])

    # Coin packages
    op.create_table(
        'coin_packages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('coins', sa.Integer(), nullable=False),
        sa.Column('bonus_coins', sa.Integer(), server_default='0'),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), server_default="'KRW'"),
        sa.Column('is_best_value', sa.Boolean(), server_default='false'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('stripe_price_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )


def downgrade():
    op.drop_table('coin_packages')
    op.drop_table('payments')
    op.drop_table('payment_methods')
    op.drop_index('ix_subscriptions_stripe_id', 'subscriptions')
    op.drop_column('subscriptions', 'stripe_customer_id')
    op.drop_column('subscriptions', 'stripe_subscription_id')
    op.drop_column('subscriptions', 'trial_end')
    op.drop_column('subscriptions', 'cancelled_at')
    op.drop_column('subscriptions', 'cancel_at_period_end')
    op.drop_column('subscriptions', 'current_period_end')
    op.drop_column('subscriptions', 'current_period_start')
    op.drop_column('subscriptions', 'billing_cycle')
    op.drop_column('subscriptions', 'plan_id')
    op.drop_table('subscription_plans')
