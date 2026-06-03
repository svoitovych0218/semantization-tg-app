"""add daily_word table

Revision ID: 002
Revises: 001
Create Date: 2026-06-03 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "daily_word",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("word", sa.String(length=100), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("embedding", ARRAY(sa.Float(precision=24)), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date", name="uq_daily_word_date"),
    )


def downgrade() -> None:
    op.drop_table("daily_word")
