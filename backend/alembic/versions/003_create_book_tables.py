"""Create additional book tables

Revision ID: 003
Revises: 002
Create Date: 2024-01-01

Note: books and user_books tables already exist in 001_initial.
This migration is kept for chain continuity but does nothing.
"""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # books and user_books already exist in 001_initial_schema
    pass


def downgrade():
    pass
