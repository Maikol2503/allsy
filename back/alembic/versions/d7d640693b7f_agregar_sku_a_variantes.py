"""agregar sku a variantes

Revision ID: d7d640693b7f
Revises: crear_ventas
Create Date: 2026-01-07 14:13:34.043729

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7d640693b7f'
down_revision: Union[str, Sequence[str], None] = 'crear_ventas'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "variantes",
        sa.Column("sku", sa.String(100), nullable=True)
    )
    op.create_unique_constraint(
        "uq_variantes_sku",
        "variantes",
        ["sku"]
    )

def downgrade():
    op.drop_constraint("uq_variantes_sku", "variantes", type_="unique")
    op.drop_column("variantes", "sku")
