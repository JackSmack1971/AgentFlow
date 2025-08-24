"""enhance user security with encryption and audit fields"""

from __future__ import annotations

import os
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "0004_enhance_user_security"
down_revision = "0003_add_otp_secret"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add security enhancements to users table."""

    # Add audit fields
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("users", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=text("(now() at time zone 'utc')")))
    op.add_column("users", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=text("(now() at time zone 'utc')")))
    op.add_column("users", sa.Column("last_login", sa.DateTime(timezone=True), nullable=True))

    # Add account security fields
    op.add_column("users", sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("account_locked_until", sa.DateTime(timezone=True), nullable=True))

    # Add soft delete field
    op.add_column("users", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    # Modify otp_secret column to accommodate encrypted data
    op.alter_column("users", "otp_secret", type_=sa.String(length=255))

    # Remove server defaults after adding columns
    op.alter_column("users", "is_active", server_default=None)
    op.alter_column("users", "created_at", server_default=None)
    op.alter_column("users", "updated_at", server_default=None)
    op.alter_column("users", "failed_login_attempts", server_default=None)

    # Create trigger to automatically update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = (now() at time zone 'utc');
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    op.execute("""
        CREATE TRIGGER update_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Remove security enhancements from users table."""

    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_users_updated_at ON users")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Remove new columns
    op.drop_column("users", "deleted_at")
    op.drop_column("users", "account_locked_until")
    op.drop_column("users", "failed_login_attempts")
    op.drop_column("users", "last_login")
    op.drop_column("users", "updated_at")
    op.drop_column("users", "created_at")
    op.drop_column("users", "is_active")

    # Revert otp_secret column length
    op.alter_column("users", "otp_secret", type_=sa.String(length=32))