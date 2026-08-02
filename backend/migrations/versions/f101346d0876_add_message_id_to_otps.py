"""Initial schema — create all tables

Revision ID: f101346d0876
Revises: 
Create Date: 2026-08-02 06:11:30.713793

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'f101346d0876'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all core tables."""

    # --- targets ---
    op.create_table(
        'targets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('provider', sa.Enum('GMAIL', 'YAHOO', 'OTHER', name='providerenum'), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'EXPIRED', 'RATE_LIMITED', 'IDLE', name='targetstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_targets_email', 'targets', ['email'], unique=True)

    # --- credentials ---
    op.create_table(
        'credentials',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('target_id', UUID(as_uuid=True), sa.ForeignKey('targets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=True),
        sa.Column('oauth_refresh_token', sa.Text(), nullable=True),
        sa.Column('oauth_access_token', sa.Text(), nullable=True),
        sa.Column('token_expiry', sa.DateTime(), nullable=True),
        sa.Column('captured_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
    )
    op.create_index('ix_credentials_target_id', 'credentials', ['target_id'])

    # --- monitoring_sessions ---
    op.create_table(
        'monitoring_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('target_id', UUID(as_uuid=True), sa.ForeignKey('targets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('started_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('last_checked_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('status', sa.Enum('POLLING', 'ERROR', 'STOPPED', 'COMPLETED', name='sessionstatus'), nullable=False),
        sa.Column('error_log', sa.Text(), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), default=0, nullable=False),
    )
    op.create_index('ix_monitoring_sessions_target_id', 'monitoring_sessions', ['target_id'])

    # --- received_otps ---
    op.create_table(
        'received_otps',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('target_id', UUID(as_uuid=True), sa.ForeignKey('targets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('monitoring_sessions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('message_id', sa.String(), nullable=True),
        sa.Column('sender', sa.String(), nullable=True),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('body_snippet', sa.Text(), nullable=True),
        sa.Column('extracted_code', sa.String(), nullable=False),
        sa.Column('confidence', sa.String(), nullable=True),
        sa.Column('received_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('is_read', sa.Boolean(), default=False, nullable=False),
    )
    op.create_index('ix_received_otps_target_id', 'received_otps', ['target_id'])
    op.create_index('ix_received_otps_session_id', 'received_otps', ['session_id'])
    op.create_index('ix_received_otps_extracted_code', 'received_otps', ['extracted_code'])
    op.create_unique_constraint('uq_received_otps_message_id', 'received_otps', ['message_id'])


def downgrade() -> None:
    """Drop all core tables in reverse dependency order."""
    op.drop_table('received_otps')
    op.drop_table('monitoring_sessions')
    op.drop_table('credentials')
    op.drop_table('targets')

    # Clean up enum types
    op.execute("DROP TYPE IF EXISTS sessionstatus")
    op.execute("DROP TYPE IF EXISTS targetstatus")
    op.execute("DROP TYPE IF EXISTS providerenum")
