"""add otp_secret column to users"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003_add_otp_secret"
down_revision = "0002_core_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("otp_secret", sa.String(length=32), nullable=False, server_default=""),
    )
    op.alter_column("users", "otp_secret", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "otp_secret")

