"""add firebase_uid to users and make password_hash nullable

Revision ID: d5e8f2a91b3c
Revises: c3a7f1e82d4a
Create Date: 2026-09-17 06:58:00.000000+07:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d5e8f2a91b3c"
down_revision: Union[str, None] = "c3a7f1e82d4a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add firebase_uid column
    op.add_column(
        "users",
        sa.Column("firebase_uid", sa.String(length=128), nullable=True),
    )

    # Backfill existing rows with a placeholder value (their UUID as string)
    op.execute("UPDATE users SET firebase_uid = id::text WHERE firebase_uid IS NULL")

    # Now make it NOT NULL and add unique index
    op.alter_column("users", "firebase_uid", nullable=False)
    op.create_unique_constraint("uq_users_firebase_uid", "users", ["firebase_uid"])
    op.create_index("ix_users_firebase_uid", "users", ["firebase_uid"])

    # Make password_hash nullable (no longer required with Firebase)
    op.alter_column("users", "password_hash", nullable=True)


def downgrade() -> None:
    op.alter_column("users", "password_hash", nullable=False)
    op.drop_index("ix_users_firebase_uid", table_name="users")
    op.drop_constraint("uq_users_firebase_uid", "users", type_="unique")
    op.drop_column("users", "firebase_uid")
