"""replace check result status_code with status enum

Revision ID: cab98c47055f
Revises: 308f957067dd
Create Date: 2026-08-22 18:30:56.886714

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cab98c47055f'
down_revision = '308f957067dd'
branch_labels = None
depends_on = None


def upgrade():
    result_status = sa.Enum('SUCCESS', 'FAIL', name='resultstatus')
    result_status.create(op.get_bind())

    op.add_column('check_results', sa.Column('status', result_status, nullable=False))
    op.drop_column('check_results', 'status_code')


def downgrade():
    op.add_column('check_results', sa.Column('status_code', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_column('check_results', 'status')

    sa.Enum(name='resultstatus').drop(op.get_bind())
