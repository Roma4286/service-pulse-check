"""rename users.name to username and index check_results.service_id

Revision ID: 6f15a4b6c8f7
Revises: 4948e2af2e59
Create Date: 2026-09-08 13:45:25.270401

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6f15a4b6c8f7'
down_revision = '4948e2af2e59'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_check_results_service_id', 'check_results', ['service_id'], unique=False)

    op.alter_column('users', 'name', new_column_name='username')
    op.execute('ALTER TABLE users RENAME CONSTRAINT users_name_key TO users_username_key')


def downgrade():
    op.execute('ALTER TABLE users RENAME CONSTRAINT users_username_key TO users_name_key')
    op.alter_column('users', 'username', new_column_name='name')

    op.drop_index('ix_check_results_service_id', table_name='check_results')
