"""agregar sku a productos

Revision ID: a3eb5a0441df
Revises: d7d640693b7f
Create Date: 2026-01-07 14:19:15.435267

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3eb5a0441df'
down_revision: Union[str, Sequence[str], None] = 'd7d640693b7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # agregar columna SKU a productos
    op.add_column(
        'productos',
        sa.Column('sku', sa.String(100), nullable=True)
    )
    # crear restricción única
    op.create_unique_constraint('uq_productos_sku', 'productos', ['sku'])


def downgrade():
    op.drop_constraint('uq_productos_sku', 'productos', type_='unique')
    op.drop_column('productos', 'sku')