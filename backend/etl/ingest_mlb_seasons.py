from pybaseball import batting_stats
import pandas as pd
from backend.database import SessionLocal
from backend.models import MLBPlayerSeason
from sqlalchemy import and_, cast, String
import datetime
import time

START_YEAR = 2011
END_YEAR = datetime.datetime.now().year

# Helper: clean stats dict for JSON
def clean_stats_json(stats):
    return {k: (None if pd.isna(v) else v) for k, v in stats.items()}

# Helper: upsert MLB player season
def upsert_mlb_player_season(session, name, team, year, position, stats_json):
    existing = session.query(MLBPlayerSeason).filter(
        and_(
            MLBPlayerSeason.name == name,
            MLBPlayerSeason.team == team,
            MLBPlayerSeason.year == year
        )
    ).first()
    if existing:
        existing.position = position
        existing.stats_json = stats_json
    else:
        s = MLBPlayerSeason(
            name=name,
            team=team,
            year=year,
            position=position,
            stats_json=stats_json
        )
        session.add(s)
    session.commit()

def main():
    session = SessionLocal()
    for year in range(START_YEAR, END_YEAR + 1):
        print(f"Fetching MLB batting stats for {year}...")
        try:
            df = batting_stats(year)
        except Exception as e:
            print(f"Failed to fetch for {year}: {e}")
            continue
        for _, row in df.iterrows():
            name = row.get('Name') or row.get('player_name') or ''
            team = row.get('Team') or row.get('team') or ''
            position = row.get('Pos') or row.get('position') or ''
            stats_json = clean_stats_json(row.to_dict())
            upsert_mlb_player_season(session, name, team, year, position, stats_json)
        time.sleep(1)
    print("Done ingesting MLB player seasons.")

if __name__ == "__main__":
    main() 