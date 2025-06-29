import requests
import pandas as pd
from backend.database import SessionLocal
from backend.models import Prospect
from sqlalchemy import and_
import time

def clean_stats_json(stats):
    return {k: (None if pd.isna(v) else v) for k, v in stats.items()}

YEAR = 2023
LEVEL = 'MiLB'

# Helper: upsert prospect
def upsert_prospect(session, name, team, position, stats_json):
    existing = session.query(Prospect).filter(
        and_(
            Prospect.name == name,
            Prospect.organization == team,
            Prospect.level == LEVEL,
        )
    ).first()
    if existing:
        existing.position = position
        existing.stats_json = stats_json
    else:
        p = Prospect(
            name=name,
            school=None,
            level=LEVEL,
            position=position,
            stats_json=stats_json,
            graduation_year=None,
            organization=team
        )
        session.add(p)
    session.commit()

def scrape_milb_batting_leaders(year):
    url = f"https://www.baseball-reference.com/register/leader.cgi?type=bat&id=milb&year={year}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch data for {year}: {response.status_code}")
        return None
    tables = pd.read_html(response.text)
    df = tables[0]
    df['Year'] = year
    return df

def main():
    session = SessionLocal()
    print(f"Scraping MiLB batting leaders for {YEAR}...")
    df = scrape_milb_batting_leaders(YEAR)
    if df is None:
        return
    for _, row in df.iterrows():
        name = row.get('Name') or row.get('Player') or ''
        team = row.get('Tm') or row.get('Team') or ''
        position = row.get('Pos') or row.get('Position') or ''
        stats_json = clean_stats_json(row.to_dict())
        upsert_prospect(session, name, team, position, stats_json)
    print("Done ingesting MiLB prospects.")

if __name__ == "__main__":
    main() 