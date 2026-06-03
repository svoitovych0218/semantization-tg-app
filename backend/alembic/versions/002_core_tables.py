"""core tables: user, chat, user_chat, guess

Revision ID: 003
Revises: 002
Create Date: 2026-06-03 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("telegram_id", sa.BigInteger, primary_key=True),
        sa.Column("first_name", sa.String(64), nullable=False),
        sa.Column("username", sa.String(64), nullable=True),
    )

    op.create_table(
        "chat",
        sa.Column("telegram_id", sa.BigInteger, primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "user_chat",
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("user.telegram_id"), primary_key=True),
        sa.Column("chat_id", sa.BigInteger, sa.ForeignKey("chat.telegram_id"), primary_key=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "guess",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("user.telegram_id"), nullable=False),
        sa.Column("word_date", sa.Date, sa.ForeignKey("daily_word.date"), nullable=False),
        sa.Column("guessed_word", sa.String(100), nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("guessed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "word_date", "guessed_word", name="uq_guess_per_word"),
    )


def downgrade() -> None:
    op.drop_table("guess")
    op.drop_table("user_chat")
    op.drop_table("chat")
    op.drop_table("user")
