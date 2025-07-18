"""add player_ratings table

Revision ID: 5156f7519737
Revises: f2435961f991
Create Date: 2025-07-08 13:50:09.138044

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5156f7519737'
down_revision: Union[str, Sequence[str], None] = 'f2435961f991'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('teams',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('abbreviation', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('abbreviation')
    )
    op.create_table('batting_stats',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.Integer(), nullable=True),
    sa.Column('year', sa.String(), nullable=True),
    sa.Column('team', sa.String(), nullable=True),
    sa.Column('league', sa.String(), nullable=True),
    sa.Column('age', sa.String(), nullable=True),
    sa.Column('war', sa.Float(), nullable=True),
    sa.Column('g', sa.Integer(), nullable=True),
    sa.Column('pa', sa.Integer(), nullable=True),
    sa.Column('ab', sa.Integer(), nullable=True),
    sa.Column('r', sa.Integer(), nullable=True),
    sa.Column('h', sa.Integer(), nullable=True),
    sa.Column('doubles', sa.Integer(), nullable=True),
    sa.Column('triples', sa.Integer(), nullable=True),
    sa.Column('hr', sa.Integer(), nullable=True),
    sa.Column('rbi', sa.Integer(), nullable=True),
    sa.Column('sb', sa.Integer(), nullable=True),
    sa.Column('cs', sa.Integer(), nullable=True),
    sa.Column('bb', sa.Integer(), nullable=True),
    sa.Column('so', sa.Integer(), nullable=True),
    sa.Column('ba', sa.String(), nullable=True),
    sa.Column('obp', sa.String(), nullable=True),
    sa.Column('slg', sa.String(), nullable=True),
    sa.Column('ops', sa.String(), nullable=True),
    sa.Column('ops_plus', sa.Integer(), nullable=True),
    sa.Column('roba', sa.String(), nullable=True),
    sa.Column('rbat_plus', sa.Integer(), nullable=True),
    sa.Column('tb', sa.Integer(), nullable=True),
    sa.Column('gidp', sa.Integer(), nullable=True),
    sa.Column('hbp', sa.Integer(), nullable=True),
    sa.Column('sh', sa.Integer(), nullable=True),
    sa.Column('sf', sa.Integer(), nullable=True),
    sa.Column('ibb', sa.Integer(), nullable=True),
    sa.Column('pos', sa.String(), nullable=True),
    sa.Column('awards', sa.String(), nullable=True),
    sa.Column('rbat', sa.Float(), nullable=True),
    sa.Column('rbaser', sa.Float(), nullable=True),
    sa.Column('rdp', sa.Float(), nullable=True),
    sa.Column('rfield', sa.Float(), nullable=True),
    sa.Column('rpos', sa.Float(), nullable=True),
    sa.Column('raa', sa.Float(), nullable=True),
    sa.Column('waa', sa.Float(), nullable=True),
    sa.Column('rrep', sa.Float(), nullable=True),
    sa.Column('rar', sa.Float(), nullable=True),
    sa.Column('waa_wl_pct', sa.String(), nullable=True),
    sa.Column('wl_162_pct', sa.String(), nullable=True),
    sa.Column('owar', sa.Float(), nullable=True),
    sa.Column('dwar', sa.Float(), nullable=True),
    sa.Column('orar', sa.Float(), nullable=True),
    sa.Column('babip', sa.String(), nullable=True),
    sa.Column('iso', sa.String(), nullable=True),
    sa.Column('hr_pct', sa.String(), nullable=True),
    sa.Column('so_pct', sa.String(), nullable=True),
    sa.Column('bb_pct', sa.String(), nullable=True),
    sa.Column('ev', sa.String(), nullable=True),
    sa.Column('hardh_pct', sa.String(), nullable=True),
    sa.Column('ld_pct', sa.String(), nullable=True),
    sa.Column('gb_pct', sa.String(), nullable=True),
    sa.Column('fb_pct', sa.String(), nullable=True),
    sa.Column('gb_fb', sa.String(), nullable=True),
    sa.Column('pull_pct', sa.String(), nullable=True),
    sa.Column('cent_pct', sa.String(), nullable=True),
    sa.Column('oppo_pct', sa.String(), nullable=True),
    sa.Column('wpa', sa.String(), nullable=True),
    sa.Column('cwpa', sa.String(), nullable=True),
    sa.Column('re24', sa.String(), nullable=True),
    sa.Column('rs_pct', sa.String(), nullable=True),
    sa.Column('sb_pct', sa.String(), nullable=True),
    sa.Column('xbt_pct', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('player_id', 'year', 'team', name='_battingstat_uc')
    )
    op.create_table('fielding_stats',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.Integer(), nullable=True),
    sa.Column('year', sa.String(), nullable=True),
    sa.Column('team', sa.String(), nullable=True),
    sa.Column('league', sa.String(), nullable=True),
    sa.Column('age', sa.String(), nullable=True),
    sa.Column('g', sa.Integer(), nullable=True),
    sa.Column('gs', sa.Integer(), nullable=True),
    sa.Column('inn', sa.String(), nullable=True),
    sa.Column('po', sa.Integer(), nullable=True),
    sa.Column('a', sa.Integer(), nullable=True),
    sa.Column('e', sa.Integer(), nullable=True),
    sa.Column('dp', sa.Integer(), nullable=True),
    sa.Column('fp', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('player_id', 'year', 'team', name='_fieldingstat_uc')
    )
    op.create_table('games',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('home_team_id', sa.Integer(), nullable=True),
    sa.Column('away_team_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['away_team_id'], ['teams.id'], ),
    sa.ForeignKeyConstraint(['home_team_id'], ['teams.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('pitching_stats',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.Integer(), nullable=True),
    sa.Column('year', sa.String(), nullable=True),
    sa.Column('team', sa.String(), nullable=True),
    sa.Column('league', sa.String(), nullable=True),
    sa.Column('age', sa.String(), nullable=True),
    sa.Column('agedif', sa.String(), nullable=True),
    sa.Column('level', sa.String(), nullable=True),
    sa.Column('aff', sa.String(), nullable=True),
    sa.Column('w', sa.Integer(), nullable=True),
    sa.Column('l', sa.Integer(), nullable=True),
    sa.Column('wl_pct', sa.String(), nullable=True),
    sa.Column('era', sa.String(), nullable=True),
    sa.Column('ra9', sa.String(), nullable=True),
    sa.Column('g', sa.Integer(), nullable=True),
    sa.Column('gs', sa.Integer(), nullable=True),
    sa.Column('gf', sa.Integer(), nullable=True),
    sa.Column('cg', sa.Integer(), nullable=True),
    sa.Column('sho', sa.Integer(), nullable=True),
    sa.Column('sv', sa.Integer(), nullable=True),
    sa.Column('ip', sa.String(), nullable=True),
    sa.Column('h', sa.Integer(), nullable=True),
    sa.Column('r', sa.Integer(), nullable=True),
    sa.Column('er', sa.Integer(), nullable=True),
    sa.Column('hr', sa.Integer(), nullable=True),
    sa.Column('bb', sa.Integer(), nullable=True),
    sa.Column('ibb', sa.Integer(), nullable=True),
    sa.Column('so', sa.Integer(), nullable=True),
    sa.Column('hbp', sa.Integer(), nullable=True),
    sa.Column('bk', sa.Integer(), nullable=True),
    sa.Column('wp', sa.Integer(), nullable=True),
    sa.Column('bf', sa.Integer(), nullable=True),
    sa.Column('whip', sa.String(), nullable=True),
    sa.Column('h9', sa.String(), nullable=True),
    sa.Column('hr9', sa.String(), nullable=True),
    sa.Column('bb9', sa.String(), nullable=True),
    sa.Column('so9', sa.String(), nullable=True),
    sa.Column('so_w', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('player_id', 'year', 'team', name='_pitchingstat_uc')
    )
    op.create_table('player_bio',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.Integer(), nullable=True),
    sa.Column('field_name', sa.String(), nullable=True),
    sa.Column('field_value', sa.String(), nullable=True),
    sa.Column('source_url', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('player_ratings',
    sa.Column('player_id', sa.Integer(), nullable=False),
    sa.Column('overall_rating', sa.Float(), nullable=True),
    sa.Column('potential_rating', sa.Float(), nullable=True),
    sa.Column('confidence_score', sa.Float(), nullable=True),
    sa.Column('player_type', sa.String(), nullable=True),
    sa.Column('last_updated', sa.DateTime(), nullable=True),
    sa.Column('contact_left', sa.Float(), nullable=True),
    sa.Column('contact_right', sa.Float(), nullable=True),
    sa.Column('power_left', sa.Float(), nullable=True),
    sa.Column('power_right', sa.Float(), nullable=True),
    sa.Column('vision', sa.Float(), nullable=True),
    sa.Column('discipline', sa.Float(), nullable=True),
    sa.Column('fielding', sa.Float(), nullable=True),
    sa.Column('arm_strength', sa.Float(), nullable=True),
    sa.Column('arm_accuracy', sa.Float(), nullable=True),
    sa.Column('speed', sa.Float(), nullable=True),
    sa.Column('stealing', sa.Float(), nullable=True),
    sa.Column('k_rating', sa.Float(), nullable=True),
    sa.Column('bb_rating', sa.Float(), nullable=True),
    sa.Column('gb_rating', sa.Float(), nullable=True),
    sa.Column('hr_rating', sa.Float(), nullable=True),
    sa.Column('command_rating', sa.Float(), nullable=True),
    sa.Column('historical_overalls', sa.JSON(), nullable=True),
    sa.Column('team', sa.String(), nullable=True),
    sa.Column('level', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
    sa.PrimaryKeyConstraint('player_id')
    )
    op.create_table('stat_tables',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.Integer(), nullable=True),
    sa.Column('caption', sa.String(), nullable=True),
    sa.Column('table_type', sa.String(), nullable=True),
    sa.Column('source_url', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('atbats',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('game_id', sa.Integer(), nullable=True),
    sa.Column('batter_id', sa.Integer(), nullable=True),
    sa.Column('pitcher_id', sa.Integer(), nullable=True),
    sa.Column('inning', sa.Integer(), nullable=True),
    sa.Column('result', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['batter_id'], ['players.id'], ),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
    sa.ForeignKeyConstraint(['pitcher_id'], ['players.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('player_game_grades',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.Integer(), nullable=True),
    sa.Column('game_id', sa.Integer(), nullable=True),
    sa.Column('grade', sa.Float(), nullable=True),
    sa.Column('notes', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('stat_rows',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('stat_table_id', sa.Integer(), nullable=True),
    sa.Column('row_index', sa.Integer(), nullable=True),
    sa.Column('row_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['stat_table_id'], ['stat_tables.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('pitches',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('game_id', sa.Integer(), nullable=True),
    sa.Column('pitcher_id', sa.Integer(), nullable=True),
    sa.Column('batter_id', sa.Integer(), nullable=True),
    sa.Column('at_bat_id', sa.Integer(), nullable=True),
    sa.Column('inning', sa.Integer(), nullable=True),
    sa.Column('pitch_number', sa.Integer(), nullable=True),
    sa.Column('pitch_type', sa.String(), nullable=True),
    sa.Column('pitch_result', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('release_speed', sa.Float(), nullable=True),
    sa.Column('release_spin_rate', sa.Float(), nullable=True),
    sa.Column('plate_x', sa.Float(), nullable=True),
    sa.Column('plate_z', sa.Float(), nullable=True),
    sa.Column('zone', sa.Integer(), nullable=True),
    sa.Column('is_strike', sa.Boolean(), nullable=True),
    sa.Column('is_ball', sa.Boolean(), nullable=True),
    sa.Column('is_called_correctly', sa.Boolean(), nullable=True),
    sa.Column('x0', sa.Float(), nullable=True),
    sa.Column('y0', sa.Float(), nullable=True),
    sa.Column('z0', sa.Float(), nullable=True),
    sa.Column('vx0', sa.Float(), nullable=True),
    sa.Column('vy0', sa.Float(), nullable=True),
    sa.Column('vz0', sa.Float(), nullable=True),
    sa.Column('ax', sa.Float(), nullable=True),
    sa.Column('ay', sa.Float(), nullable=True),
    sa.Column('az', sa.Float(), nullable=True),
    sa.Column('sz_top', sa.Float(), nullable=True),
    sa.Column('sz_bot', sa.Float(), nullable=True),
    sa.Column('launch_speed', sa.Float(), nullable=True),
    sa.Column('launch_angle', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['at_bat_id'], ['atbats.id'], ),
    sa.ForeignKeyConstraint(['batter_id'], ['players.id'], ),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
    sa.ForeignKeyConstraint(['pitcher_id'], ['players.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('pitches')
    op.drop_table('stat_rows')
    op.drop_table('player_game_grades')
    op.drop_table('atbats')
    op.drop_table('stat_tables')
    op.drop_table('player_ratings')
    op.drop_table('player_bio')
    op.drop_table('pitching_stats')
    op.drop_table('games')
    op.drop_table('fielding_stats')
    op.drop_table('batting_stats')
    op.drop_table('teams')
    # ### end Alembic commands ###
