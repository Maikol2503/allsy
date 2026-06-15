"""Agregar columnas de compra a productos

Revision ID: c4f7580685e5
Revises: 
Create Date: 2026-01-04 22:16:33.478168
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c4f7580685e5'
down_revision = None  # <--- reemplaza con tu última revisión si existe
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Agregar columnas de compra a productos."""
    op.add_column('productos', sa.Column('lugar_compra', sa.String(length=150), nullable=True))
    op.add_column('productos', sa.Column('fecha_compra', sa.Date(), nullable=True))
    op.add_column('productos', sa.Column('precio_compra', sa.Float(), nullable=True))


def downgrade() -> None:
    """Revertir la adición de columnas."""
    op.drop_column('productos', 'precio_compra')
    op.drop_column('productos', 'fecha_compra')
    op.drop_column('productos', 'lugar_compra')