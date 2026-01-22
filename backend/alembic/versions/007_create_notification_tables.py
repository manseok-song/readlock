"""Create notification tables

Revision ID: 007
Revises: 006
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Notifications
    op.create_table(
        'notifications',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('data', JSON, nullable=True),
        sa.Column('is_read', sa.Boolean(), server_default='false'),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_user_unread', 'notifications', ['user_id', 'is_read'])

    # Notification settings
    op.create_table(
        'notification_settings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('push_enabled', sa.Boolean(), server_default='true'),
        sa.Column('reading_reminder', sa.Boolean(), server_default='true'),
        sa.Column('reading_reminder_time', sa.String(5), server_default="'21:00'"),
        sa.Column('social_notifications', sa.Boolean(), server_default='true'),
        sa.Column('marketing_notifications', sa.Boolean(), server_default='false'),
        sa.Column('streak_reminder', sa.Boolean(), server_default='true'),
        sa.Column('goal_notifications', sa.Boolean(), server_default='true'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # Device tokens
    op.create_table(
        'device_tokens',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(500), nullable=False, unique=True),
        sa.Column('platform', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_device_tokens_user_id', 'device_tokens', ['user_id'])


def downgrade():
    op.drop_table('device_tokens')
    op.drop_table('notification_settings')
    op.drop_table('notifications')
