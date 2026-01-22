"""Create additional community tables

Revision ID: 005
Revises: 004
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Note: quotes, quote_likes, reviews already exist in 001_initial

    # Review likes
    op.create_table(
        'review_likes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('review_id', UUID(as_uuid=True), sa.ForeignKey('reviews.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('review_id', 'user_id', name='uq_review_likes'),
    )

    # Comments (for both quotes and reviews)
    op.create_table(
        'comments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parent_type', sa.String(20), nullable=False),
        sa.Column('parent_id', UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_comments_parent', 'comments', ['parent_type', 'parent_id'])


def downgrade():
    op.drop_table('comments')
    op.drop_table('review_likes')
