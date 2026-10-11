"""index check_results by service_id, created_at, id

Revision ID: 41a80e62ca97
Revises: 6f15a4b6c8f7
Create Date: 2026-10-11 12:29:35.758626

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "41a80e62ca97"
down_revision = "6f15a4b6c8f7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_check_results_service_id_created_at_id",
        "check_results",
        ["service_id", "created_at", "id"],
        unique=False,
    )
    # service_id is the leading column of the new index, so the old one is redundant.
    op.drop_index("ix_check_results_service_id", table_name="check_results")


def downgrade():
    op.create_index(
        "ix_check_results_service_id", "check_results", ["service_id"], unique=False
    )
    op.drop_index(
        "ix_check_results_service_id_created_at_id", table_name="check_results"
    )
