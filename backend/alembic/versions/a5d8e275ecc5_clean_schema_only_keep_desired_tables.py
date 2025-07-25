"""Clean schema: only keep desired tables

Revision ID: a5d8e275ecc5
Revises: 5156f7519737
Create Date: 2025-07-09 12:31:49.432891

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a5d8e275ecc5'
down_revision: Union[str, Sequence[str], None] = '5156f7519737'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("DROP TABLE IF EXISTS atbats CASCADE")
    op.execute("DROP TABLE IF EXISTS pitching_stats CASCADE")
    op.execute("DROP TABLE IF EXISTS teams CASCADE")
    op.execute("DROP TABLE IF EXISTS fielding_stats CASCADE")
    op.execute("DROP TABLE IF EXISTS games CASCADE")
    op.execute("DROP TABLE IF EXISTS pitches CASCADE")
    op.execute("DROP TABLE IF EXISTS player_game_grades CASCADE")
    op.execute("DROP TABLE IF EXISTS batting_stats CASCADE")
    op.execute("DROP TABLE IF EXISTS player_bio CASCADE")
    op.execute("DROP TABLE IF EXISTS stat_rows CASCADE")
    op.execute("DROP TABLE IF EXISTS stat_tables CASCADE")
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('batting_stats',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('player_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('year', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('team', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('league', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('age', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('war', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('g', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('pa', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('ab', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('r', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('h', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('doubles', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('triples', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('hr', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('rbi', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('sb', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('cs', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('bb', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('so', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('ba', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('obp', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('slg', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('ops', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('ops_plus', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('roba', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('rbat_plus', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('tb', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('gidp', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('hbp', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('sh', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('sf', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('ibb', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('pos', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('awards', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('rbat', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('rbaser', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('rdp', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('rfield', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('rpos', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('raa', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('waa', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('rrep', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('rar', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('waa_wl_pct', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('wl_162_pct', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('owar', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('dwar', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('orar', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('babip', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('iso', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('hr_pct', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('so_pct', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('bb_pct', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('ev', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('hardh_pct', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('ld_pct', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('gb_pct', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('fb_pct', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('gb_fb', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('pull_pct', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('cent_pct', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('oppo_pct', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('wpa', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('cwpa', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('re24', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('rs_pct', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('sb_pct', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('xbt_pct', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], name=op.f('batting_stats_player_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('batting_stats_pkey')),
    sa.UniqueConstraint('player_id', 'year', 'team', name=op.f('_battingstat_uc'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_table('player_game_grades',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('player_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('game_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('grade', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('notes', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], name=op.f('player_game_grades_game_id_fkey')),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], name=op.f('player_game_grades_player_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('player_game_grades_pkey'))
    )
    op.create_table('pitches',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('game_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('pitcher_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('batter_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('at_bat_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('inning', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('pitch_number', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('pitch_type', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('pitch_result', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('release_speed', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('release_spin_rate', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('plate_x', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('plate_z', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('zone', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('is_strike', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('is_ball', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('is_called_correctly', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('x0', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('y0', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('z0', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('vx0', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('vy0', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('vz0', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('ax', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('ay', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('az', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('sz_top', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('sz_bot', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('launch_speed', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('launch_angle', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['at_bat_id'], ['atbats.id'], name=op.f('pitches_at_bat_id_fkey')),
    sa.ForeignKeyConstraint(['batter_id'], ['players.id'], name=op.f('pitches_batter_id_fkey')),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], name=op.f('pitches_game_id_fkey')),
    sa.ForeignKeyConstraint(['pitcher_id'], ['players.id'], name=op.f('pitches_pitcher_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('pitches_pkey'))
    )
    op.create_table('games',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('games_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('date', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('home_team_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('away_team_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['away_team_id'], ['teams.id'], name='games_away_team_id_fkey'),
    sa.ForeignKeyConstraint(['home_team_id'], ['teams.id'], name='games_home_team_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='games_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_table('fielding_stats',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('player_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('year', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('team', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('league', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('age', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('g', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('gs', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('inn', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('po', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('a', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('e', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('dp', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('fp', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], name=op.f('fielding_stats_player_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('fielding_stats_pkey')),
    sa.UniqueConstraint('player_id', 'year', 'team', name=op.f('_fieldingstat_uc'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_table('teams',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('teams_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('abbreviation', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='teams_pkey'),
    sa.UniqueConstraint('abbreviation', name='teams_abbreviation_key', postgresql_include=[], postgresql_nulls_not_distinct=False),
    postgresql_ignore_search_path=False
    )
    op.create_table('pitching_stats',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('player_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('year', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('team', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('league', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('age', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('agedif', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('level', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('aff', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('w', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('l', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('wl_pct', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('era', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('ra9', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('g', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('gs', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('gf', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('cg', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('sho', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('sv', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('ip', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('h', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('r', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('er', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('hr', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('bb', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('ibb', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('so', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('hbp', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('bk', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('wp', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('bf', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('whip', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('h9', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('hr9', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('bb9', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('so9', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('so_w', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], name=op.f('pitching_stats_player_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('pitching_stats_pkey')),
    sa.UniqueConstraint('player_id', 'year', 'team', name=op.f('_pitchingstat_uc'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_table('atbats',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('game_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('batter_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('pitcher_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('inning', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('result', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['batter_id'], ['players.id'], name=op.f('atbats_batter_id_fkey')),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], name=op.f('atbats_game_id_fkey')),
    sa.ForeignKeyConstraint(['pitcher_id'], ['players.id'], name=op.f('atbats_pitcher_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('atbats_pkey'))
    )
    # ### end Alembic commands ###
