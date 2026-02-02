"""Add ticket relations, time tracking, and CSAT fields

Revision ID: 20260202_ticket_enhancements
Revises: 20260109_add_ticket_soft_delete
Create Date: 2026-02-02

This migration adds:
1. CSAT (Customer Satisfaction) fields to tickets table
2. ticket_relations table for linking related tickets
3. ticket_time_entries table for time tracking

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260202_ticket_enhancements'
down_revision = '20260109_soft_delete'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add CSAT fields to tickets table
    op.add_column('tickets', sa.Column('rating', sa.Integer(), nullable=True))
    op.add_column('tickets', sa.Column('rating_comment', sa.Text(), nullable=True))
    op.add_column('tickets', sa.Column('rating_submitted_at', sa.DateTime(), nullable=True))

    # 2. Create ticket_relations table
    op.create_table(
        'ticket_relations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_ticket_id', sa.Integer(), nullable=False),
        sa.Column('target_ticket_id', sa.Integer(), nullable=False),
        sa.Column('relation_type', sa.String(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['source_ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_ticket_id', 'target_ticket_id', 'relation_type', name='uq_ticket_relation')
    )
    op.create_index('ix_ticket_relations_id', 'ticket_relations', ['id'])
    op.create_index('ix_ticket_relations_source_ticket_id', 'ticket_relations', ['source_ticket_id'])
    op.create_index('ix_ticket_relations_target_ticket_id', 'ticket_relations', ['target_ticket_id'])
    op.create_index('ix_ticket_relations_relation_type', 'ticket_relations', ['relation_type'])
    op.create_index('ix_ticket_relations_source_target', 'ticket_relations', ['source_ticket_id', 'target_ticket_id'])

    # 3. Create ticket_time_entries table
    op.create_table(
        'ticket_time_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('minutes', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('work_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('entry_type', sa.String(), nullable=True, server_default='work'),
        sa.Column('is_billable', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('hourly_rate', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ticket_time_entries_id', 'ticket_time_entries', ['id'])
    op.create_index('ix_ticket_time_entries_ticket_id', 'ticket_time_entries', ['ticket_id'])
    op.create_index('ix_ticket_time_entries_user_id', 'ticket_time_entries', ['user_id'])
    op.create_index('ix_ticket_time_entries_user_date', 'ticket_time_entries', ['user_id', 'work_date'])


def downgrade() -> None:
    # Drop ticket_time_entries table
    op.drop_index('ix_ticket_time_entries_user_date', table_name='ticket_time_entries')
    op.drop_index('ix_ticket_time_entries_user_id', table_name='ticket_time_entries')
    op.drop_index('ix_ticket_time_entries_ticket_id', table_name='ticket_time_entries')
    op.drop_index('ix_ticket_time_entries_id', table_name='ticket_time_entries')
    op.drop_table('ticket_time_entries')

    # Drop ticket_relations table
    op.drop_index('ix_ticket_relations_source_target', table_name='ticket_relations')
    op.drop_index('ix_ticket_relations_relation_type', table_name='ticket_relations')
    op.drop_index('ix_ticket_relations_target_ticket_id', table_name='ticket_relations')
    op.drop_index('ix_ticket_relations_source_ticket_id', table_name='ticket_relations')
    op.drop_index('ix_ticket_relations_id', table_name='ticket_relations')
    op.drop_table('ticket_relations')

    # Remove CSAT fields from tickets
    op.drop_column('tickets', 'rating_submitted_at')
    op.drop_column('tickets', 'rating_comment')
    op.drop_column('tickets', 'rating')
