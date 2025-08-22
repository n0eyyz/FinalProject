"""contents.processed_at -> timestamptz

Revision ID: a3aafd2b327a
Revises: 604eca58f22a
Create Date: 2025-08-13 17:57:56.116879

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3aafd2b327a'
down_revision: Union[str, Sequence[str], None] = '604eca58f22a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "contents",
        "processed_at",
        type_=sa.DateTime(timezone=True),
        postgresql_using="processed_at AT TIME ZONE 'UTC'",
        existing_type=sa.DateTime(timezone=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "contents",
        "processed_at",
        type_=sa.DateTime(timezone=False),
        postgresql_using="processed_at",  # 단순 제거
        existing_type=sa.DateTime(timezone=True)
    )
