"""add bref_id and bio_json to player

Revision ID: xxxx
Revises: 1ffbb910b300
Create Date: 2025-06-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'xxxx'
down_revision: Union[str, Sequence[str], None] = '1ffbb910b300'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('players', sa.Column('bref_id', sa.String(), unique=True, index=True))
    op.add_column('players', sa.Column('bio_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('players', 'bio_json')
    op.drop_column('players', 'bref_id') 