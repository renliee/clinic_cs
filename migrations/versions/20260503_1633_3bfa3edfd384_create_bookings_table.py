"""Migration files (DB restructure instruction in python lang, alembic auto generate from newest Base.metadata)
Revision ID: 3bfa3edfd384
Revises: 
Create Date: 2026-05-03 16:33:25.048625+00:00
"""
#migration upgrade and downgrade act like a linked list
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


#revision: alembic version identifiers.
revision: str = '3bfa3edfd384'
down_revision: Union[str, None] = None #points to the previous db version 
branch_labels: Union[str, Sequence[str], None] = None #if this version has branches
depends_on: Union[str, Sequence[str], None] = None #if this version depends to a diff alembic verison 

#upgrade: execute the changes that was planned
def upgrade() -> None:
    op.create_table('bookings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('booking_id', sa.String(length=20), nullable=False),
    sa.Column('user_id', sa.String(length=100), nullable=False),
    sa.Column('nama', sa.String(length=100), nullable=False),
    sa.Column('lokasi', sa.String(length=100), nullable=False),
    sa.Column('treatment', sa.String(length=100), nullable=False),
    sa.Column('tanggal', sa.Date(), nullable=False),
    sa.Column('jam', sa.Time(), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'CONFIRMED', 'CANCELED', 'COMPLETED', name='booking_status'), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bookings_booking_id'), 'bookings', ['booking_id'], unique=True)
    op.create_index(op.f('ix_bookings_created_at'), 'bookings', ['created_at'], unique=False)
    op.create_index(op.f('ix_bookings_status'), 'bookings', ['status'], unique=False)
    op.create_index(op.f('ix_bookings_user_id'), 'bookings', ['user_id'], unique=False)

#cancel the migration then go back to db previous version (this is the first migration so delete all index and drop db table)
def downgrade() -> None:
    op.drop_index(op.f('ix_bookings_user_id'), table_name='bookings')
    op.drop_index(op.f('ix_bookings_status'), table_name='bookings')
    op.drop_index(op.f('ix_bookings_created_at'), table_name='bookings')
    op.drop_index(op.f('ix_bookings_booking_id'), table_name='bookings')
    op.drop_table('bookings')