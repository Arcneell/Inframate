"""Add email integration tables and fields

Revision ID: 20260204_email
Revises: 20260202_add_ticket_relations_time_csat
Create Date: 2026-02-04

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '20260204_email'
down_revision = '20260202_ticket_enhancements'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create email_configurations table
    op.create_table(
        'email_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('provider_type', sa.String(), nullable=False),  # smtp_imap, microsoft_365
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('is_inbound_enabled', sa.Boolean(), server_default='false'),
        sa.Column('is_outbound_enabled', sa.Boolean(), server_default='true'),
        # SMTP settings (outbound)
        sa.Column('smtp_host', sa.String(), nullable=True),
        sa.Column('smtp_port', sa.Integer(), server_default='587'),
        sa.Column('smtp_username', sa.String(), nullable=True),
        sa.Column('smtp_password', sa.String(), nullable=True),  # EncryptedString in model
        sa.Column('smtp_use_tls', sa.Boolean(), server_default='true'),
        # IMAP settings (inbound)
        sa.Column('imap_host', sa.String(), nullable=True),
        sa.Column('imap_port', sa.Integer(), server_default='993'),
        sa.Column('imap_username', sa.String(), nullable=True),
        sa.Column('imap_password', sa.String(), nullable=True),  # EncryptedString in model
        sa.Column('imap_use_ssl', sa.Boolean(), server_default='true'),
        sa.Column('imap_folder', sa.String(), server_default="'INBOX'"),
        # Microsoft 365 settings
        sa.Column('m365_tenant_id', sa.String(), nullable=True),
        sa.Column('m365_client_id', sa.String(), nullable=True),
        sa.Column('m365_client_secret', sa.String(), nullable=True),  # EncryptedString in model
        sa.Column('m365_mailbox', sa.String(), nullable=True),
        # Common sender settings
        sa.Column('from_email', sa.String(), nullable=True),
        sa.Column('from_name', sa.String(), server_default="'Inframate'"),
        sa.Column('reply_to_email', sa.String(), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['entity_id'], ['entities.id'], ondelete='SET NULL')
    )
    op.create_index('ix_email_configurations_id', 'email_configurations', ['id'])
    op.create_index('ix_email_configurations_entity_id', 'email_configurations', ['entity_id'])

    # Create sent_emails table
    op.create_table(
        'sent_emails',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email_config_id', sa.Integer(), nullable=True),
        sa.Column('ticket_id', sa.Integer(), nullable=True),
        sa.Column('comment_id', sa.Integer(), nullable=True),
        # RFC 5322 headers
        sa.Column('message_id', sa.String(), nullable=False, unique=True),
        sa.Column('in_reply_to', sa.String(), nullable=True),
        sa.Column('references', sa.Text(), nullable=True),
        # Recipient info
        sa.Column('recipient_email', sa.String(), nullable=False),
        sa.Column('recipient_user_id', sa.Integer(), nullable=True),
        # Email content
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('body_text', sa.Text(), nullable=True),
        sa.Column('body_html', sa.Text(), nullable=True),
        # Classification
        sa.Column('email_type', sa.String(), nullable=False),  # ticket_created, ticket_assigned, etc.
        # Status tracking
        sa.Column('status', sa.String(), server_default="'pending'"),  # pending, sent, failed
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0'),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['email_config_id'], ['email_configurations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['comment_id'], ['ticket_comments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['recipient_user_id'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('ix_sent_emails_id', 'sent_emails', ['id'])
    op.create_index('ix_sent_emails_message_id', 'sent_emails', ['message_id'], unique=True)
    op.create_index('ix_sent_emails_ticket_id', 'sent_emails', ['ticket_id'])
    op.create_index('ix_sent_emails_email_type', 'sent_emails', ['email_type'])
    op.create_index('ix_sent_emails_status', 'sent_emails', ['status'])

    # Create inbound_emails table
    op.create_table(
        'inbound_emails',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email_config_id', sa.Integer(), nullable=True),
        # RFC 5322 headers
        sa.Column('message_id', sa.String(), nullable=False, unique=True),
        sa.Column('in_reply_to', sa.String(), nullable=True),
        sa.Column('references', sa.Text(), nullable=True),
        # Sender/recipient
        sa.Column('from_email', sa.String(), nullable=False),
        sa.Column('from_name', sa.String(), nullable=True),
        sa.Column('to_email', sa.String(), nullable=False),
        # Content
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('body_text', sa.Text(), nullable=True),
        sa.Column('body_html', sa.Text(), nullable=True),
        sa.Column('raw_headers', JSONB(), nullable=True),
        # Processing status
        sa.Column('processing_status', sa.String(), server_default="'pending'"),  # pending, processed, ignored, error
        sa.Column('processing_result', JSONB(), nullable=True),  # {ticket_id, comment_id, action}
        sa.Column('error_message', sa.Text(), nullable=True),
        # Timestamps
        sa.Column('received_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['email_config_id'], ['email_configurations.id'], ondelete='SET NULL')
    )
    op.create_index('ix_inbound_emails_id', 'inbound_emails', ['id'])
    op.create_index('ix_inbound_emails_message_id', 'inbound_emails', ['message_id'], unique=True)
    op.create_index('ix_inbound_emails_in_reply_to', 'inbound_emails', ['in_reply_to'])
    op.create_index('ix_inbound_emails_from_email', 'inbound_emails', ['from_email'])
    op.create_index('ix_inbound_emails_processing_status', 'inbound_emails', ['processing_status'])

    # Add email_message_id and sla_warning_sent to tickets table
    op.add_column('tickets', sa.Column('email_message_id', sa.String(), nullable=True))
    op.add_column('tickets', sa.Column('sla_warning_sent', sa.Boolean(), server_default='false'))
    op.create_index('ix_tickets_email_message_id', 'tickets', ['email_message_id'])

    # Add email fields to ticket_comments table
    op.add_column('ticket_comments', sa.Column('email_message_id', sa.String(), nullable=True))
    op.add_column('ticket_comments', sa.Column('is_email_reply', sa.Boolean(), server_default='false'))
    op.create_index('ix_ticket_comments_email_message_id', 'ticket_comments', ['email_message_id'])


def downgrade() -> None:
    # Remove indexes from ticket_comments
    op.drop_index('ix_ticket_comments_email_message_id', 'ticket_comments')
    # Remove columns from ticket_comments
    op.drop_column('ticket_comments', 'is_email_reply')
    op.drop_column('ticket_comments', 'email_message_id')

    # Remove indexes from tickets
    op.drop_index('ix_tickets_email_message_id', 'tickets')
    # Remove columns from tickets
    op.drop_column('tickets', 'sla_warning_sent')
    op.drop_column('tickets', 'email_message_id')

    # Drop inbound_emails table
    op.drop_index('ix_inbound_emails_processing_status', 'inbound_emails')
    op.drop_index('ix_inbound_emails_from_email', 'inbound_emails')
    op.drop_index('ix_inbound_emails_in_reply_to', 'inbound_emails')
    op.drop_index('ix_inbound_emails_message_id', 'inbound_emails')
    op.drop_index('ix_inbound_emails_id', 'inbound_emails')
    op.drop_table('inbound_emails')

    # Drop sent_emails table
    op.drop_index('ix_sent_emails_status', 'sent_emails')
    op.drop_index('ix_sent_emails_email_type', 'sent_emails')
    op.drop_index('ix_sent_emails_ticket_id', 'sent_emails')
    op.drop_index('ix_sent_emails_message_id', 'sent_emails')
    op.drop_index('ix_sent_emails_id', 'sent_emails')
    op.drop_table('sent_emails')

    # Drop email_configurations table
    op.drop_index('ix_email_configurations_entity_id', 'email_configurations')
    op.drop_index('ix_email_configurations_id', 'email_configurations')
    op.drop_table('email_configurations')
