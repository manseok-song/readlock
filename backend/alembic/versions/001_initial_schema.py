"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-01-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "postgis"')

    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('provider', sa.String(50), nullable=False, server_default='local'),
        sa.Column('provider_id', sa.String(255), nullable=True),
        sa.Column('fcm_token', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
    )

    # User profiles table
    op.create_table(
        'user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'),
                  unique=True, nullable=False),
        sa.Column('nickname', sa.String(50), unique=True, nullable=False),
        sa.Column('bio', sa.Text, nullable=True),
        sa.Column('profile_image', sa.String(500), nullable=True),
        sa.Column('reading_goal_min', sa.Integer, server_default='30'),
        sa.Column('is_public', sa.Boolean, server_default='true'),
        sa.Column('level', sa.Integer, server_default='1'),
        sa.Column('exp', sa.Integer, server_default='0'),
        sa.Column('coins', sa.Integer, server_default='0'),
        sa.Column('premium_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
    )

    # Books table
    op.create_table(
        'books',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('isbn', sa.String(20), unique=True, nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('author', sa.String(255), nullable=False),
        sa.Column('publisher', sa.String(255), nullable=True),
        sa.Column('published_date', sa.Date, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('cover_image', sa.String(500), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('page_count', sa.Integer, nullable=True),
        sa.Column('naver_link', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
    )

    # User books (bookshelf)
    op.create_table(
        'user_books',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('book_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('books.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('current_page', sa.Integer, server_default='0'),
        sa.Column('total_pages', sa.Integer, nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.UniqueConstraint('user_id', 'book_id', name='uq_user_book'),
    )

    # Reading sessions
    op.create_table(
        'reading_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_book_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('user_books.id', ondelete='CASCADE'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_sec', sa.Integer, nullable=True),
        sa.Column('pages_read', sa.Integer, server_default='0'),
        sa.Column('was_locked', sa.Boolean, server_default='false'),
        sa.Column('platform', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
    )

    # Quotes
    op.create_table(
        'quotes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('book_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('books.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('page_number', sa.Integer, nullable=True),
        sa.Column('memo', sa.Text, nullable=True),
        sa.Column('likes_count', sa.Integer, server_default='0'),
        sa.Column('is_public', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
    )

    # Quote likes
    op.create_table(
        'quote_likes',
        sa.Column('quote_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('quotes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('quote_id', 'user_id'),
    )

    # Reviews
    op.create_table(
        'reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('book_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('books.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.Numeric(2, 1), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('has_spoiler', sa.Boolean, server_default='false'),
        sa.Column('likes_count', sa.Integer, server_default='0'),
        sa.Column('is_public', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.UniqueConstraint('user_id', 'book_id', name='uq_user_review'),
    )

    # Follows
    op.create_table(
        'follows',
        sa.Column('follower_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('following_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('follower_id', 'following_id'),
        sa.CheckConstraint('follower_id != following_id', name='ck_no_self_follow'),
    )

    # Subscriptions
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plan', sa.String(50), nullable=False),
        sa.Column('platform', sa.String(20), nullable=False),
        sa.Column('store_txn_id', sa.String(255), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
    )

    # Create indexes
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_provider', 'users', ['provider', 'provider_id'])
    op.create_index('idx_profiles_nickname', 'user_profiles', ['nickname'])
    op.create_index('idx_books_isbn', 'books', ['isbn'])
    op.create_index('idx_user_books_user_status', 'user_books', ['user_id', 'status'])
    op.create_index('idx_sessions_user_book', 'reading_sessions', ['user_book_id'])
    op.create_index('idx_sessions_date', 'reading_sessions', ['started_at'])
    op.create_index('idx_quotes_user', 'quotes', ['user_id'])
    op.create_index('idx_quotes_book', 'quotes', ['book_id'])
    op.create_index('idx_reviews_book', 'reviews', ['book_id'])
    op.create_index('idx_follows_follower', 'follows', ['follower_id'])
    op.create_index('idx_follows_following', 'follows', ['following_id'])
    op.create_index('idx_subscriptions_user', 'subscriptions', ['user_id'])


def downgrade() -> None:
    op.drop_table('subscriptions')
    op.drop_table('follows')
    op.drop_table('reviews')
    op.drop_table('quote_likes')
    op.drop_table('quotes')
    op.drop_table('reading_sessions')
    op.drop_table('user_books')
    op.drop_table('books')
    op.drop_table('user_profiles')
    op.drop_table('users')
