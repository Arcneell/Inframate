"""Add M365 user_email and folder_id fields

Revision ID: 20260204_m365_ext
Revises: 20260204_email
Create Date: 2026-02-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260204_m365_ext'
down_revision = '20260204_email'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add m365_user_email column to email_configurations
    op.add_column('email_configurations', sa.Column('m365_user_email', sa.String(), nullable=True))

    # Add m365_folder_id column to email_configurations
    op.add_column('email_configurations', sa.Column('m365_folder_id', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove m365_folder_id column
    op.drop_column('email_configurations', 'm365_folder_id')

    # Remove m365_user_email column
    op.drop_column('email_configurations', 'm365_user_email')
