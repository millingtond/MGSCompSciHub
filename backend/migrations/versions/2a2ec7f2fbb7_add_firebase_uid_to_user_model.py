"""Add firebase_uid to User model

Revision ID: 2a2ec7f2fbb7
Revises: a415719ae705
Create Date: 2025-05-24 21:25:46.959673

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2a2ec7f2fbb7'
down_revision = 'a415719ae705'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('firebase_uid', sa.String(length=128), nullable=True))
        batch_op.create_index(batch_op.f('ix_users_firebase_uid'), ['firebase_uid'], unique=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_firebase_uid'))
        batch_op.drop_column('firebase_uid')

    # ### end Alembic commands ###
