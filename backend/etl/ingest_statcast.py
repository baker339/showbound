import pandas as pd
from pybaseball import statcast
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import models
from datetime import datetime, timedelta
import os
import sys
from backend.scripts.empty_database import main as empty_db_main

def convert_na_to_none(value):
    """Convert pandas NA values to None for database insertion"""
    if pd.isna(value):
        return None
    return value

def get_or_create_team(session, name, abbr):
    team = session.query(models.Team).filter_by(abbreviation=abbr).first()
    if not team:
        team = models.Team(name=name, abbreviation=abbr)
        session.add(team)
        session.commit()
        session.refresh(team)
    return team

def get_or_create_player(session, player_id, team_id, name=None, position=None):
    player = session.query(models.Player).filter_by(id=player_id).first()
    if not player:
        player_name = name if name else f"Player_{player_id}"
        player = models.Player(id=player_id, name=player_name, team_id=team_id, position=position)
        session.add(player)
        session.commit()
        session.refresh(player)
    else:
        # Update name/team/position if changed
        updated = False
        if name and player.name != name:
            player.name = name
            updated = True
        if team_id and player.team_id != team_id:
            player.team_id = team_id
            updated = True
        if position and player.position != position:
            player.position = position
            updated = True
        if updated:
            session.commit()
    return player

def get_or_create_game(session, game_pk, date, home_team_id, away_team_id):
    game = session.query(models.Game).filter_by(id=game_pk).first()
    if not game:
        game = models.Game(id=game_pk, date=date, home_team_id=home_team_id, away_team_id=away_team_id)
        session.add(game)
        session.commit()
        session.refresh(game)
    return game

def get_or_create_atbat(session, ab_id, game_id, batter_id, pitcher_id, inning, result):
    atbat = session.query(models.AtBat).filter_by(id=ab_id).first()
    if not atbat:
        atbat = models.AtBat(id=ab_id, game_id=game_id, batter_id=batter_id, pitcher_id=pitcher_id, inning=inning, result=result)
        session.add(atbat)
        session.commit()
        session.refresh(atbat)
    return atbat

def ingest_statcast(start_date: str, end_date: str):
    print(f"Fetching Statcast data from {start_date} to {end_date}")
    df = statcast(start_date, end_date)
    if df.empty:
        print("No data found.")
        return
    
    # Debug: Print DataFrame info
    print(f"DataFrame shape: {df.shape}")
    print("DataFrame columns:")
    print(df.columns.tolist())
    print("\nFirst few rows:")
    print(df.head())
    
    # Check for required columns
    required_columns = ['home_team', 'away_team', 'pitcher', 'batter', 'game_pk', 'game_date', 
                       'inning_topbot', 'inning', 'at_bat_number', 'pitch_number']
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"\nERROR: Missing required columns: {missing_columns}")
        print("Available columns that might be similar:")
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['team', 'pitcher', 'batter', 'game', 'inning']):
                print(f"  - {col}")
        return
    
    session = SessionLocal()
    try:
        for _, row in df.iterrows():
            # Teams - use team abbreviations as both name and abbreviation for now
            home_team = get_or_create_team(session, row['home_team'], row['home_team'])
            away_team = get_or_create_team(session, row['away_team'], row['away_team'])
            
            # Player names from DataFrame if available
            pitcher_name = None
            batter_name = None
            if 'pitcher_name' in df.columns:
                pitcher_name = row.get('pitcher_name')
            elif 'player_name' in df.columns:
                # Statcast uses 'player_name' for both pitcher and batter, so we need to check context
                # We'll use player_name for both if available, but this is a limitation of the data
                pitcher_name = row.get('player_name')
            if 'batter_name' in df.columns:
                batter_name = row.get('batter_name')
            elif 'player_name' in df.columns:
                batter_name = row.get('player_name')
            
            # Players - use player names if available
            pitcher = get_or_create_player(
                session,
                row['pitcher'],
                home_team.id if row['inning_topbot']=='Bot' else away_team.id,
                name=pitcher_name
            )
            batter = get_or_create_player(
                session,
                row['batter'],
                away_team.id if row['inning_topbot']=='Bot' else home_team.id,
                name=batter_name
            )
            
            # Game
            game = get_or_create_game(session, row['game_pk'], pd.to_datetime(row['game_date']), home_team.id, away_team.id)
            
            # AtBat
            ab_id = row['at_bat_number'] + row['game_pk'] * 1000  # unique per game
            atbat = get_or_create_atbat(session, ab_id, row['game_pk'], batter.id, pitcher.id, row['inning'], convert_na_to_none(row.get('events')))
            
            # Pitch
            pitch = models.Pitch(
                game_id=game.id,
                pitcher_id=pitcher.id,
                batter_id=batter.id,
                at_bat_id=atbat.id,
                inning=row['inning'],
                pitch_number=row['pitch_number'],
                pitch_type=convert_na_to_none(row.get('pitch_type')),
                pitch_result=convert_na_to_none(row.get('type')),
                description=convert_na_to_none(row.get('description')),
                release_speed=convert_na_to_none(row.get('release_speed')),
                release_spin_rate=convert_na_to_none(row.get('release_spin_rate')),
                plate_x=convert_na_to_none(row.get('plate_x')),
                plate_z=convert_na_to_none(row.get('plate_z')),
                zone=convert_na_to_none(row.get('zone')),
                is_strike=row.get('type') in ['S', 'C'] if row.get('type') else False,
                is_ball=row.get('type') == 'B' if row.get('type') else False,
                is_called_correctly=None,  # To be computed later
                x0=convert_na_to_none(row.get('vx0')),  # Note: Statcast uses vx0, vy0, vz0 for initial velocities
                y0=convert_na_to_none(row.get('vy0')),
                z0=convert_na_to_none(row.get('vz0')),
                vx0=convert_na_to_none(row.get('vx0')),
                vy0=convert_na_to_none(row.get('vy0')),
                vz0=convert_na_to_none(row.get('vz0')),
                ax=convert_na_to_none(row.get('ax')),
                ay=convert_na_to_none(row.get('ay')),
                az=convert_na_to_none(row.get('az')),
                sz_top=convert_na_to_none(row.get('sz_top')),
                sz_bot=convert_na_to_none(row.get('sz_bot')),
                launch_speed=convert_na_to_none(row.get('launch_speed')),
                launch_angle=convert_na_to_none(row.get('launch_angle')),
            )
            session.add(pitch)
        session.commit()
        print(f"Ingested {len(df)} pitches.")
    except Exception as e:
        print(f"Error during ingestion: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def main():
    # Empty the database before ingestion
    empty_db_main()

    session = SessionLocal()
    try:
        latest_game = session.query(models.Game).order_by(models.Game.date.desc()).first()
        if latest_game is None:
            start_date_dt = datetime(2025, 3, 1)
        else:
            # Add one day to the latest game date
            start_date_dt = latest_game.date + timedelta(days=1)
        # End date is yesterday (UTC)
        end_date_dt = datetime.utcnow().date() - timedelta(days=1)
        # Convert to string format for statcast (YYYY-MM-DD)
        start_date = start_date_dt.strftime('%Y-%m-%d')
        end_date = end_date_dt.strftime('%Y-%m-%d')
        if start_date_dt.date() > end_date_dt:
            print(f"No new data to ingest. Latest game in DB: {latest_game.date if latest_game else 'None'}, yesterday: {end_date}")
            return
        print(f"Ingesting Statcast data from {start_date} to {end_date}")
        ingest_statcast(start_date, end_date)
    finally:
        session.close()

if __name__ == '__main__':
    main() 