import requests
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import Prospect
from sqlalchemy import and_, cast, String
import datetime
import time

START_YEAR = 2011
END_YEAR = datetime.datetime.now().year
LEVEL = 'NCAA'

# Helper: upsert prospect
def upsert_prospect(session, name, school, year, level, position, stats_json):
    existing = session.query(Prospect).filter(
        and_(
            Prospect.name == name,
            Prospect.school == school,
            Prospect.level == level,
            cast(Prospect.stats_json['Year'], String) == str(year)
        )
    ).first()
    if existing:
        existing.position = position
        existing.stats_json = stats_json
    else:
        p = Prospect(
            name=name,
            school=school,
            level=level,
            position=position,
            stats_json=stats_json
        )
        session.add(p)
    session.commit()

def scrape_ncaa_batting_leaders(year, url=None):
    if url is None:
        url = f"https://www.baseball-reference.com/register/leader.cgi?type=bat&year={year}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch data for {year}: {response.status_code}")
        return None
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'id': 'leaders'})
    if table is None:
        tables = soup.find_all('table')
        if not tables:
            print(f"No tables found for {year}")
            return None
        table = tables[0]
    df = pd.read_html(str(table))[0]
    # Flatten multi-index columns
    df.columns = [col[1] if isinstance(col, tuple) else col for col in df.columns]
    # Add year column
    df['Year'] = year
    return df

def clean_stats_json(stats):
    # Convert all NaN/pd.NA to None for Postgres JSON compatibility
    return {k: (None if pd.isna(v) else v) for k, v in stats.items()}

def main():
    session = SessionLocal()
    for year in range(START_YEAR, END_YEAR + 1):
        print(f"Scraping NCAA batting leaders for {year}...")
        df = scrape_ncaa_batting_leaders(year)
        if df is None:
            continue
        for _, row in df.iterrows():
            name = row.get('Name') or row.get('Player') or ''
            school = row.get('Tm') or row.get('School') or ''
            position = row.get('Pos') or row.get('Position') or ''
            stats_json = row.to_dict()
            stats_json = clean_stats_json(stats_json)
            upsert_prospect(session, name, school, year, LEVEL, position, stats_json)
        # Be polite to the server
        time.sleep(1)
    print("Done scraping all years.")

if __name__ == "__main__":
    main() 