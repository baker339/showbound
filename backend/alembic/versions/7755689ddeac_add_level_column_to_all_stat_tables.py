"""Add level column to all stat tables

Revision ID: 7755689ddeac
Revises: a5d8e275ecc5
Create Date: 2025-07-09 15:00:20.346226

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7755689ddeac'
down_revision: Union[str, Sequence[str], None] = 'a5d8e275ecc5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('advanced_batting_stats', sa.Column('level', sa.String(), nullable=True))
    op.add_column('advanced_pitching_stats', sa.Column('level', sa.String(), nullable=True))
    op.add_column('standard_batting_stats', sa.Column('level', sa.String(), nullable=True))
    op.add_column('standard_fielding_stats', sa.Column('level', sa.String(), nullable=True))
    op.add_column('standard_pitching_stats', sa.Column('level', sa.String(), nullable=True))
    op.add_column('value_batting_stats', sa.Column('level', sa.String(), nullable=True))
    op.add_column('value_pitching_stats', sa.Column('level', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('value_pitching_stats', 'level')
    op.drop_column('value_batting_stats', 'level')
    op.drop_column('standard_pitching_stats', 'level')
    op.drop_column('standard_fielding_stats', 'level')
    op.drop_column('standard_batting_stats', 'level')
    op.drop_column('advanced_pitching_stats', 'level')
    op.drop_column('advanced_batting_stats', 'level')
    # ### end Alembic commands ###
