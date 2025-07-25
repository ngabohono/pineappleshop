"""Added Category model

Revision ID: 938ffcc68609
Revises: 181718d96b69
Create Date: 2025-05-30 05:22:50.911296

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '938ffcc68609'
down_revision = '181718d96b69'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('category',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('category')
    # ### end Alembic commands ###
