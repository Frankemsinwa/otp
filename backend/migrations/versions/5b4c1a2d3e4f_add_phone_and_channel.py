"""add_phone_and_channel_columns

Revision ID: 5b4c1a2d3e4f
Revises: f101346d0876
Create Date: 2026-08-08 02:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b4c1a2d3e4f'
down_revision: Union[str, None] = 'f101346d0876'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add phone_number to targets
    op.add_column('targets', sa.Column('phone_number', sa.String(), nullable=True))
    op.create_index(op.f('ix_targets_phone_number'), 'targets', ['phone_number'], unique=False)

    # Add channel to received_otps
    op.add_column('received_otps', sa.Column('channel', sa.String(), server_default='email', nullable=False))


def downgrade() -> None:
    op.drop_column('received_otps', 'channel')
    
    op.drop_index(op.f('ix_targets_phone_number'), table_name='targets')
    op.drop_column('targets', 'phone_number')
