"""mover_fecha_registro_a_stock_unit

Revision ID: f3c49f5cef15
Revises: a3eb5a0441df
Create Date: 2026-06-02 23:39:43.001732

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3c49f5cef15'
down_revision: Union[str, Sequence[str], None] = 'a3eb5a0441df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Agregar columnas a stock_units
    op.add_column('stock_units', sa.Column('fecha_compra', sa.Date(), nullable=True))
    op.add_column('stock_units', sa.Column('fecha_registro', sa.DateTime(timezone=True), nullable=True))
    
    # 2. Copiar los datos históricos desde stock_configs hacia stock_units
    op.execute("""
        UPDATE stock_units su
        INNER JOIN stock_configs sc ON su.stock_config_id = sc.id
        SET su.fecha_compra = sc.fecha_compra,
            su.fecha_registro = sc.fecha_registro
    """)
    
    # 3. Eliminar las columnas viejas de stock_configs
    op.drop_column('stock_configs', 'fecha_compra')
    op.drop_column('stock_configs', 'fecha_registro')
    op.drop_column('stock_configs', 'fecha_actualizacion')


def downgrade() -> None:
    # 1. Volver a crear columnas en stock_configs
    op.add_column('stock_configs', sa.Column('fecha_compra', sa.Date(), nullable=True))
    op.add_column('stock_configs', sa.Column('fecha_registro', sa.DateTime(timezone=True), nullable=True))
    op.add_column('stock_configs', sa.Column('fecha_actualizacion', sa.DateTime(timezone=True), nullable=True))
    
    # 2. Retroceder los datos
    op.execute("""
        UPDATE stock_configs sc
        INNER JOIN stock_units su ON sc.id = su.stock_config_id
        SET sc.fecha_compra = su.fecha_compra,
            sc.fecha_registro = su.fecha_registro
    """)
    
    # 3. Borrar columnas de stock_units
    op.drop_column('stock_units', 'fecha_compra')
    op.drop_column('stock_units', 'fecha_registro')
