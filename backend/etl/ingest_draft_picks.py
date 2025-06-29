import requests
import pandas as pd
from backend.database import SessionLocal
from backend.models import DraftPick
from sqlalchemy import and_
import time
import re

def clean_stats_json(stats):
    return {k: (None if pd.isna(v) else v) for k, v in stats.items()}

def clean_player_name(name):
    if not name:
        return ''
    name = re.sub(r'\(minors\)', '', name)
    return name.strip()

def extract_school(drafted_out_of):
    if not drafted_out_of or pd.isna(drafted_out_of):
        return ''
    # Remove location in parentheses
    return re.sub(r'\s*\([^)]*\)', '', drafted_out_of).strip()

START_YEAR = 2011
END_YEAR = pd.Timestamp.now().year

# Helper: upsert draft pick
def upsert_draft_pick(session, player_name, school, draft_year, round_, pick_overall, mlb_team, mlb_player_name, extra_json):
    existing = session.query(DraftPick).filter(
        and_(
            DraftPick.player_name == player_name,
            DraftPick.draft_year == draft_year,
            DraftPick.round == round_,
            DraftPick.pick_overall == pick_overall
        )
    ).first()
    if existing:
        existing.school = school
        existing.mlb_team = mlb_team
        existing.mlb_player_name = mlb_player_name
        existing.extra_json = extra_json
    else:
        d = DraftPick(
            player_name=player_name,
            school=school,
            draft_year=draft_year,
            round=round_,
            pick_overall=pick_overall,
            mlb_team=mlb_team,
            mlb_player_name=mlb_player_name,
            extra_json=extra_json
        )
        session.add(d)
    session.commit()

def scrape_draft_year(year):
    url = f"https://www.baseball-reference.com/draft/?year_ID={year}&draft_type=junreg"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch draft data for {year}: {response.status_code}")
        return None
    tables = pd.read_html(response.text)
    df = tables[0]
    # Filter: only 4Yr college and correct year
    df = df[(df['Type'] == '4Yr') & (df['Year'] == year)]
    # Clean player name and school
    df['Player'] = df['Name'].apply(clean_player_name)
    df['School'] = df['Drafted Out of'].apply(extract_school)
    df = df[df['Player'].notna() & df['Player'].str.strip().ne('') & df['School'].notna() & df['School'].str.strip().ne('')]
    df['Year'] = year
    return df

def main():
    session = SessionLocal()
    for year in range(START_YEAR, END_YEAR + 1):
        print(f"Scraping MLB draft picks for {year}...")
        df = scrape_draft_year(year)
        if df is None:
            continue
        for _, row in df.iterrows():
            player_name = row.get('Player')
            drafted_out_of = row.get('Drafted Out of')
            school = extract_school(drafted_out_of)
            round_ = str(row.get('Rnd') or row.get('Round') or '')
            pick_overall = row.get('RdPck') or row.get('OvPck') or row.get('Pick') or None
            mlb_team = row.get('Tm') or row.get('Team') or ''
            mlb_player_name = row.get('MLB Player') or row.get('MLB Debut') or ''
            extra_json = clean_stats_json(row.to_dict())
            upsert_draft_pick(session, player_name, school, year, round_, pick_overall, mlb_team, mlb_player_name, extra_json)
        time.sleep(1)
    print("Done ingesting draft picks.")

if __name__ == "__main__":
    main() 