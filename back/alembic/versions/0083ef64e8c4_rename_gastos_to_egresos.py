"""rename_gastos_to_egresos

Revision ID: 0083ef64e8c4
Revises: d4190e75c423
Create Date: 2026-06-24 02:15:39.453336

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0083ef64e8c4'
down_revision: Union[str, Sequence[str], None] = 'd4190e75c423'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table('gastos', 'egresos')


def downgrade() -> None:
    """Downgrade schema."""
    op.rename_table('egresos', 'gastos')
