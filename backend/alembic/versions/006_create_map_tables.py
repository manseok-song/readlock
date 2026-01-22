"""Create map tables

Revision ID: 006
Revises: 005
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # Bookstores
    op.create_table(
        'bookstores',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('address', sa.String(500), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('website', sa.String(500), nullable=True),
        sa.Column('opening_hours', JSON, nullable=True),
        sa.Column('features', JSON, nullable=True),
        sa.Column('image_urls', JSON, nullable=True),
        sa.Column('average_rating', sa.Float(), nullable=True),
        sa.Column('review_count', sa.Integer(), server_default='0'),
        sa.Column('is_verified', sa.Boolean(), server_default='false'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_bookstores_location', 'bookstores', ['latitude', 'longitude'])
    op.create_index('ix_bookstores_name', 'bookstores', ['name'])

    # Bookstore reviews
    op.create_table(
        'bookstore_reviews',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('bookstore_id', UUID(as_uuid=True), sa.ForeignKey('bookstores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.Float(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('bookstore_id', 'user_id', name='uq_bookstore_user_review'),
    )
    op.create_index('ix_bookstore_reviews_bookstore', 'bookstore_reviews', ['bookstore_id'])

    # Bookstore favorites
    op.create_table(
        'bookstore_favorites',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('bookstore_id', UUID(as_uuid=True), sa.ForeignKey('bookstores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('bookstore_id', 'user_id', name='uq_bookstore_favorites'),
    )
    op.create_index('ix_bookstore_favorites_user', 'bookstore_favorites', ['user_id'])

    # Check-ins
    op.create_table(
        'checkins',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('bookstore_id', UUID(as_uuid=True), sa.ForeignKey('bookstores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('coins_earned', sa.Integer(), server_default='0'),
        sa.Column('exp_earned', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_checkins_user_id', 'checkins', ['user_id'])
    op.create_index('ix_checkins_bookstore_id', 'checkins', ['bookstore_id'])
    op.create_index('ix_checkins_user_date', 'checkins', ['user_id', 'created_at'])


def downgrade():
    op.drop_table('checkins')
    op.drop_table('bookstore_favorites')
    op.drop_table('bookstore_reviews')
    op.drop_table('bookstores')
