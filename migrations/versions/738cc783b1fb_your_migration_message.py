"""Your migration message

Revision ID: 738cc783b1fb
Revises: daf30c357fc9
Create Date: 2025-07-29 20:35:52.510464

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '738cc783b1fb'
down_revision: Union[str, Sequence[str], None] = 'daf30c357fc9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
