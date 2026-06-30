"""rename_es_gasto_to_es_egreso

Revision ID: 2eb3ef48e624
Revises: 0083ef64e8c4
Create Date: 2026-06-24 02:20:24.321270

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2eb3ef48e624'
down_revision: Union[str, Sequence[str], None] = '0083ef64e8c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('proveedores', 'es_gasto', new_column_name='es_egreso', existing_type=sa.Boolean())


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('proveedores', 'es_egreso', new_column_name='es_gasto', existing_type=sa.Boolean())
