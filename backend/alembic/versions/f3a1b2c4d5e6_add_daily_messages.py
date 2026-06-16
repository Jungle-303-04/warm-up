"""add daily messages

Revision ID: f3a1b2c4d5e6
Revises: d639db507c4f
Create Date: 2026-06-17 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f3a1b2c4d5e6"
down_revision: Union[str, None] = "d639db507c4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "daily_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_daily_messages_id"),
        "daily_messages",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_daily_messages_author_id"),
        "daily_messages",
        ["author_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_daily_messages_author_id"), table_name="daily_messages")
    op.drop_index(op.f("ix_daily_messages_id"), table_name="daily_messages")
    op.drop_table("daily_messages")
