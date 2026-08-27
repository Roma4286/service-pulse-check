"""add cascade to check_results service_id foreign key

Revision ID: 2be59bb2c706
Revises: 9941521cc3b1
Create Date: 2026-08-27 13:08:39.945628

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2be59bb2c706'
down_revision = '9941521cc3b1'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(op.f('fk_check_results_service_id_services'), 'check_results', type_='foreignkey')
    op.create_foreign_key(
        'fk_check_results_service_id_services', 'check_results', 'services', ['service_id'], ['id'],
        ondelete='CASCADE',
    )


def downgrade():
    op.drop_constraint(op.f('fk_check_results_service_id_services'), 'check_results', type_='foreignkey')
    op.create_foreign_key(
        'fk_check_results_service_id_services', 'check_results', 'services', ['service_id'], ['id'],
    )
