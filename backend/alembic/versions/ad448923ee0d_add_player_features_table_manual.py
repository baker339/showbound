"""Add player_features table (manual)

Revision ID: ad448923ee0d
Revises: e7cbdec1c768
Create Date: 2025-07-03 12:18:41.003236

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad448923ee0d'
down_revision: Union[str, Sequence[str], None] = 'e7cbdec1c768'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'player_features',
        sa.Column('player_id', sa.Integer(), sa.ForeignKey('players.id'), primary_key=True),
        sa.Column('raw_features', sa.PickleType(), nullable=False),
        sa.Column('normalized_features', sa.PickleType(), nullable=False),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('player_features')
