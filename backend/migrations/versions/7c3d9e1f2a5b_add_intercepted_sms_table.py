"""add_intercepted_sms_table

Creates the `intercepted_sms` table that logs all incoming SMS — not just
OTP-bearing ones — giving a full audit trail per target.

Revision ID: 7c3d9e1f2a5b
Revises: 5b4c1a2d3e4f
Create Date: 2026-08-12 03:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '7c3d9e1f2a5b'
down_revision: Union[str, None] = '5b4c1a2d3e4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'intercepted_sms',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('target_id', UUID(as_uuid=True), sa.ForeignKey('targets.id', ondelete='CASCADE'), nullable=True),
        sa.Column('sender', sa.String(), nullable=True),
        sa.Column('recipient', sa.String(), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('message_sid', sa.String(), nullable=True),
        sa.Column('received_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    )

    # Indexes — matching the model declarations
    op.create_index(op.f('ix_intercepted_sms_target_id'), 'intercepted_sms', ['target_id'], unique=False)
    op.create_index(op.f('ix_intercepted_sms_message_sid'), 'intercepted_sms', ['message_sid'], unique=True)
    op.create_index(op.f('ix_intercepted_sms_received_at'), 'intercepted_sms', ['received_at'], unique=False)
    op.create_index(op.f('ix_intercepted_sms_sender'), 'intercepted_sms', ['sender'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_intercepted_sms_sender'), table_name='intercepted_sms')
    op.drop_index(op.f('ix_intercepted_sms_received_at'), table_name='intercepted_sms')
    op.drop_index(op.f('ix_intercepted_sms_message_sid'), table_name='intercepted_sms')
    op.drop_index(op.f('ix_intercepted_sms_target_id'), table_name='intercepted_sms')
    op.drop_table('intercepted_sms')
