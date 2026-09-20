"""add student_level to users

Revision ID: c3a7f1e82d4a
Revises: bf496f6764d6
Create Date: 2026-09-16 23:04:00.000000+07:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3a7f1e82d4a"
down_revision: Union[str, None] = "bf496f6764d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("student_level", sa.String(length=10), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "student_level")
