"""add user model

Revision ID: 4948e2af2e59
Revises: 2b68404d5caf
Create Date: 2026-09-07 21:58:27.198120

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4948e2af2e59'
down_revision = '2b68404d5caf'
branch_labels = None
depends_on = None


users_table = sa.table(
    'users',
    sa.column('name', sa.String),
    sa.column('password_hash', sa.String),
)


def upgrade():
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('password_hash', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.bulk_insert(users_table, [{
        'name': 'Roman',
        'password_hash': '$argon2id$v=19$m=19456,t=2,p=1$+6dwPiLMmmABrHCMM6mRkw$F2f1KDmGHi0g14FEHlN/hRipMEOtgMmfSjIVaL5pgTc',
    }])

    op.add_column('services', sa.Column('user_id', sa.Integer(), nullable=True))
    op.execute("UPDATE services SET user_id = (SELECT id FROM users WHERE name = 'Roman')")
    op.alter_column('services', 'user_id', existing_type=sa.Integer(), nullable=False)

    op.create_foreign_key('fk_services_user_id', 'services', 'users', ['user_id'], ['id'], ondelete='CASCADE')


def downgrade():
    op.drop_constraint('fk_services_user_id', 'services', type_='foreignkey')
    op.drop_column('services', 'user_id')
    op.drop_table('users')
