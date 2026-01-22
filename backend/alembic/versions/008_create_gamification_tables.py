"""Create gamification tables

Revision ID: 008
Revises: 007
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    # Badges
    op.create_table(
        'badges',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('icon_url', sa.String(500), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('tier', sa.String(20), nullable=False),
        sa.Column('requirements', JSON, nullable=False),
        sa.Column('exp_reward', sa.Integer(), server_default='0'),
        sa.Column('coin_reward', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # User badges
    op.create_table(
        'user_badges',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('badge_id', UUID(as_uuid=True), sa.ForeignKey('badges.id', ondelete='CASCADE'), nullable=False),
        sa.Column('earned_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('user_id', 'badge_id', name='uq_user_badges'),
    )
    op.create_index('ix_user_badges_user_id', 'user_badges', ['user_id'])

    # User levels
    op.create_table(
        'user_levels',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('level', sa.Integer(), server_default='1'),
        sa.Column('current_exp', sa.Integer(), server_default='0'),
        sa.Column('total_exp', sa.Integer(), server_default='0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # Level config
    op.create_table(
        'level_configs',
        sa.Column('level', sa.Integer(), primary_key=True),
        sa.Column('required_exp', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(100), nullable=False),
        sa.Column('rewards', JSON, nullable=True),
    )

    # Exp history
    op.create_table(
        'exp_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('description', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_exp_history_user_id', 'exp_history', ['user_id'])

    # Shop items
    op.create_table(
        'shop_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('subcategory', sa.String(50), nullable=True),
        sa.Column('price_coins', sa.Integer(), nullable=False),
        sa.Column('price_real', sa.Float(), nullable=True),
        sa.Column('preview_url', sa.String(500), nullable=False),
        sa.Column('asset_data', JSON, nullable=True),
        sa.Column('is_limited', sa.Boolean(), server_default='false'),
        sa.Column('available_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('required_level', sa.Integer(), server_default='1'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_shop_items_category', 'shop_items', ['category'])

    # User inventory
    op.create_table(
        'user_inventory',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('item_id', UUID(as_uuid=True), sa.ForeignKey('shop_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('purchased_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('is_equipped', sa.Boolean(), server_default='false'),
        sa.UniqueConstraint('user_id', 'item_id', name='uq_user_inventory'),
    )
    op.create_index('ix_user_inventory_user_id', 'user_inventory', ['user_id'])

    # User coins
    op.create_table(
        'user_coins',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('balance', sa.Integer(), server_default='0'),
        sa.Column('lifetime_earned', sa.Integer(), server_default='0'),
        sa.Column('lifetime_spent', sa.Integer(), server_default='0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # Coin transactions
    op.create_table(
        'coin_transactions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('balance_after', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(20), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('description', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_coin_transactions_user_id', 'coin_transactions', ['user_id'])


def downgrade():
    op.drop_table('coin_transactions')
    op.drop_table('user_coins')
    op.drop_table('user_inventory')
    op.drop_table('shop_items')
    op.drop_table('exp_history')
    op.drop_table('level_configs')
    op.drop_table('user_levels')
    op.drop_table('user_badges')
    op.drop_table('badges')
