"""Initial schema — customers, credit_gaps, offers

Revision ID: 0001
Revises:
Create Date: 2024-01-15 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── customers ──────────────────────────────────────────────────────────────
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("mobile", sa.String(length=10), nullable=False),
        sa.Column("pan", sa.String(length=10), nullable=False),
        sa.Column("cibil_score", sa.Integer(), nullable=True),
        sa.Column("score_fetched_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mobile"),
        sa.UniqueConstraint("pan"),
    )
    op.create_index("ix_customers_id", "customers", ["id"])
    op.create_index("ix_customers_mobile", "customers", ["mobile"])
    op.create_index("ix_customers_pan", "customers", ["pan"])

    # ── credit_gaps ────────────────────────────────────────────────────────────
    op.create_table(
        "credit_gaps",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("factor", sa.String(length=255), nullable=False),
        sa.Column("current_value", sa.String(length=255), nullable=False),
        sa.Column("ideal_value", sa.String(length=255), nullable=False),
        sa.Column(
            "impact",
            sa.Enum("high", "medium", "low", name="impact_enum"),
            nullable=False,
        ),
        sa.Column("estimated_score_gain", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("action_description", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("open", "resolved", name="gapstatus"),
            nullable=False,
            server_default="open",
        ),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_credit_gaps_id", "credit_gaps", ["id"])
    op.create_index("ix_credit_gaps_customer_id", "credit_gaps", ["customer_id"])
    op.create_index("ix_credit_gaps_status", "credit_gaps", ["status"])

    # ── offers ─────────────────────────────────────────────────────────────────
    op.create_table(
        "offers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("lender", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("interest_rate", sa.Float(), nullable=False),
        sa.Column("tenure_months", sa.Integer(), nullable=False),
        sa.Column("min_score_required", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "active", "disbursed", name="offerstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_offers_id", "offers", ["id"])
    op.create_index("ix_offers_customer_id", "offers", ["customer_id"])
    op.create_index("ix_offers_status", "offers", ["status"])


def downgrade() -> None:
    op.drop_table("offers")
    op.drop_table("credit_gaps")
    op.drop_table("customers")
    # Drop named enums (MySQL handles this automatically, but good practice)
    op.execute("DROP TYPE IF EXISTS offerstatus")
    op.execute("DROP TYPE IF EXISTS gapstatus")
    op.execute("DROP TYPE IF EXISTS impact_enum")
