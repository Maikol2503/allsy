from alembic import op
import sqlalchemy as sa

revision = "crear_ventas"
down_revision = "c4f7580685e5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ventas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("producto_id", sa.Integer(), sa.ForeignKey("productos.id"), nullable=False),
        sa.Column("variante_id", sa.Integer(), sa.ForeignKey("variantes.id"), nullable=True),

        sa.Column("precio_venta", sa.Float(), nullable=False),
        sa.Column("cantidad", sa.Integer(), default=1),
        sa.Column("ganancia", sa.Float(), nullable=False),

        sa.Column("fecha_venta", sa.Date(), nullable=False),
        sa.Column("canal_venta", sa.String(50), nullable=False),
        sa.Column("comprador", sa.String(150)),
        sa.Column("vendedor", sa.String(50), nullable=False),
    )


def downgrade():
    op.drop_table("ventas")
