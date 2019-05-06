"""Change commit size.

Revision ID: 141ceff13f17
Revises: None
Create Date: 2013-07-24 00:15:10.951231

"""

# revision identifiers, used by Alembic.
revision = '141ceff13f17'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('deployments', 'commit', type_=sa.String(128),
                    existing_type=sa.String(32))


def downgrade():
    op.alter_column('deployments', 'commit', type_=sa.String(32),
                    existing_type=sa.String(128))
