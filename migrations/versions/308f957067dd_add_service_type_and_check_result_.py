"""add service type and check result foreign key

Revision ID: 308f957067dd
Revises: 39ce7ecba740
Create Date: 2026-08-22 17:05:38.609640

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '308f957067dd'
down_revision = '39ce7ecba740'
branch_labels = None
depends_on = None


def upgrade():
    service_type = sa.Enum('HTTP', 'TCP', name='servicetype')
    service_type.create(op.get_bind())

    op.add_column('services', sa.Column('type', service_type, nullable=False))
    op.create_foreign_key('fk_check_results_service_id_services', 'check_results', 'services', ['service_id'], ['id'])


def downgrade():
    op.drop_constraint('fk_check_results_service_id_services', 'check_results', type_='foreignkey')
    op.drop_column('services', 'type')

    sa.Enum(name='servicetype').drop(op.get_bind())
