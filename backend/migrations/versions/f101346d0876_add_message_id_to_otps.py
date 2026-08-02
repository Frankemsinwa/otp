"""add message_id to otps

Revision ID: f101346d0876
Revises: 
Create Date: 2026-08-02 06:11:30.713793

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f101346d0876'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('otps', sa.Column('message_id', sa.String(length=255), nullable=True))
    op.create_unique_constraint('uq_otps_message_id', 'otps', ['message_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_otps_message_id', 'otps', type_='unique')
    op.drop_column('otps', 'message_id')
