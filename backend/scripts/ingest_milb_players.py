import requests
from bs4 import BeautifulSoup, Comment
import time
import os
import sys
import argparse
import bs4
from sqlalchemy.exc import IntegrityError
from sqlalchemy import String, Integer, Float
from backend.database import SessionLocal
from backend.models import Player, StandardBattingStat, StandardPitchingStat, StandardFieldingStat
from tqdm import tqdm

# Mapping from BRef register table headers to model fields
# Updated for register page structure
BATTING_MAP = {
    'Year': 'season', 'Tm': 'team', 'Lev': 'level', 'G': 'g', 'PA': 'pa', 'AB': 'ab', 'R': 'r', 'H': 'h', '2B': 'doubles', '3B': 'triples', 'HR': 'hr', 'RBI': 'rbi', 'SB': 'sb', 'CS': 'cs', 'BB': 'bb', 'SO': 'so', 'BA': 'ba', 'OBP': 'obp', 'SLG': 'slg', 'OPS': 'ops', 'TB': 'tb', 'GDP': 'gidp', 'HBP': 'hbp', 'SH': 'sh', 'SF': 'sf', 'IBB': 'ibb', 'Age': 'age', 'Lg': 'lg', 'Aff': 'aff',
}
PITCHING_MAP = {
    'Year': 'season', 'Tm': 'team', 'Lev': 'level', 'W': 'w', 'L': 'l', 'W-L%': 'wl_pct', 'ERA': 'era', 'G': 'g', 'GS': 'gs', 'GF': 'gf', 'CG': 'cg', 'SHO': 'sho', 'SV': 'sv', 'IP': 'ip', 'H': 'h', 'R': 'r', 'ER': 'er', 'HR': 'hr', 'BB': 'bb', 'IBB': 'ibb', 'SO': 'so', 'HBP': 'hbp', 'BK': 'bk', 'WP': 'wp', 'BF': 'bf', 'ERA+': 'era_plus', 'FIP': 'fip', 'WHIP': 'whip', 'H9': 'h9', 'HR9': 'hr9', 'BB9': 'bb9', 'SO9': 'so9', 'SO/W': 'so_w', 'Age': 'age', 'Lg': 'lg', 'Aff': 'aff',
}
FIELDING_MAP = {
    'Year': 'season', 'Tm': 'team', 'Lev': 'level', 'Pos': 'pos', 'G': 'g', 'GS': 'gs', 'Inn': 'inn', 'Ch': 'ch', 'PO': 'po', 'A': 'a', 'E': 'e', 'DP': 'dp', 'Fld%': 'fld_pct', 'Rdrs': 'rdrs', 'RF/9': 'rf9', 'SB': 'sb', 'CS': 'cs', 'Age': 'age', 'Lg': 'lg', 'Aff': 'aff',
}

MLB_TEAM_KEYWORDS = [
    'majors', 'mlb', 'atlanta braves', 'arizona diamondbacks', 'baltimore orioles', 'boston red sox',
    'chicago white sox', 'chicago cubs', 'cincinnati reds', 'cleveland guardians', 'colorado rockies',
    'detroit tigers', 'houston astros', 'kansas city royals', 'los angeles angels', 'los angeles dodgers',
    'miami marlins', 'milwaukee brewers', 'minnesota twins', 'new york yankees', 'new york mets',
    'oakland athletics', 'philadelphia phillies', 'pittsburgh pirates', 'san diego padres',
    'san francisco giants', 'seattle mariners', 'st. louis cardinals', 'tampa bay rays',
    'texas rangers', 'toronto blue jays', 'washington nationals'
]

def get_soup(url):
    time.sleep(3)  # 3 second delay before each request
    resp = requests.get(url)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, 'html.parser')

def extract_bio_from_meta(soup):
    bio = {}
    meta_div = soup.find('div', id='meta')
    if not meta_div:
        return bio
    for p in meta_div.find_all('p'):
        strong = p.find('strong')
        if strong:
            label = strong.get_text(strip=True).replace(':', '')
            value = p.get_text(strip=True).replace(strong.get_text(strip=True), '').strip(': ').strip()
            bio[label] = value
    return bio

def is_major_league_team(team_str):
    if not team_str:
        return False
    team_str = team_str.lower()
    return any(keyword in team_str for keyword in MLB_TEAM_KEYWORDS)

def extract_table_from_comments(soup, table_id):
    """Extract table from HTML comments if not found in main HTML"""
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        if table_id in comment:
            comment_soup = BeautifulSoup(comment, 'html.parser')
            table = comment_soup.find('table', id=table_id)
            if table:
                return table
    return None

def normalize_team(team_str):
    if not team_str:
        return team_str
    team_str = str(team_str).strip()
    team_str = team_str.replace(' (minors)', '').replace(' (majors)', '')
    return team_str

def main():
    parser = argparse.ArgumentParser(description='Ingest minor league players from URL file')
    parser.add_argument('url_file', help='Path to the URL file (e.g., aaa_player_urls.txt)')
    parser.add_argument('--level', help='Level override (e.g., AAA, AA, A+, A, Rk)')
    args = parser.parse_args()
    
    # Determine level from filename if not provided
    level = args.level
    if not level:
        filename = os.path.basename(args.url_file)
        if 'aaa' in filename.lower():
            level = 'AAA'
        elif 'aa' in filename.lower():
            level = 'AA'
        elif 'a+' in filename.lower():
            level = 'A+'
        elif 'a_' in filename.lower() or filename.lower().startswith('a_player'):
            level = 'A'
        elif 'rk' in filename.lower():
            level = 'Rk'
        else:
            level = 'UNKNOWN'
    
    print(f"[INFO] Processing {level} players from {args.url_file}")
    
    session = SessionLocal()
    with open(args.url_file, 'r') as f:
        player_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    ingested = 0
    skipped_mlb = 0
    errors = 0
    
    # Create progress bar
    pbar = tqdm(total=len(player_urls), desc=f"Processing {level} players")
    
    for i, url in enumerate(player_urls):
        try:
            soup = get_soup(url)
            bio = extract_bio_from_meta(soup)
            
            # Extract player name
            name_tag = soup.find('h1')
            full_name = name_tag.get_text(strip=True) if name_tag else None
            if not full_name:
                pbar.set_postfix({'Status': 'No name found'})
                pbar.update(1)
                continue
            
            # Check if player already exists
            player_obj = session.query(Player).filter_by(full_name=full_name).first()
            if not player_obj:
                player_obj = Player(
                    full_name=full_name,
                    level=level,
                    source_url=url
                )
                session.add(player_obj)
                session.flush()
            
            skip_for_mlb_team = False
            stats_found = False
            
            # Parse stat tables using correct register page table IDs
            for table_id, Model, MAP in [
                ('standard_batting', StandardBattingStat, BATTING_MAP),
                ('standard_pitching', StandardPitchingStat, PITCHING_MAP),
                ('standard_fielding', StandardFieldingStat, FIELDING_MAP)
            ]:
                table = soup.find('table', id=table_id)
                if not table:
                    table = extract_table_from_comments(soup, table_id)
                
                if not isinstance(table, bs4.element.Tag):
                    continue
                
                # Find the header row that contains the actual column names
                # Register pages often have multiple header rows
                header_row = None
                for row in table.find_all('tr'):
                    if not isinstance(row, bs4.element.Tag):
                        continue
                    cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                    if 'Year' in cells and 'Tm' in cells:
                        header_row = cells
                        break
                
                if not header_row:
                    continue
                
                # Process data rows
                for row in table.find_all('tr'):
                    if not isinstance(row, bs4.element.Tag):
                        continue
                    
                    cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                    if len(cells) != len(header_row):
                        continue
                    
                    # Skip header rows
                    if cells[0] == 'Year' or not cells[0].isdigit():
                        continue
                    
                    data = dict(zip(header_row, cells))
                    
                    # Skip aggregate rows (e.g., '2 Teams', '2 Lgs')
                    if 'Tm' in data and ('Teams' in data['Tm'] or 'Lgs' in data['Tm']):
                        continue
                    
                    # Use 'Lev' for level, 'Tm' for team
                    row_level = data.get('Lev')
                    team = data.get('Tm')
                    season = data.get('Year')
                    
                    if not (row_level and team and season):
                        continue
                    
                    # Skip MLB teams
                    if is_major_league_team(team):
                        skip_for_mlb_team = True
                        break
                    
                    # Map fields using MAP
                    mapped = {MAP.get(k, k): v for k, v in data.items()}
                    
                    # Only pass valid fields to the model
                    valid_fields = set(str(c.name) for c in Model.__table__.columns)
                    filtered = {str(k): (v if v != '' else None) for k, v in mapped.items() if str(k) in valid_fields}
                    
                    # Ensure player_id is set
                    filtered['player_id'] = player_obj.id
                    
                    # Normalize team name
                    if 'team' in filtered and filtered['team']:
                        filtered['team'] = normalize_team(filtered['team'])
                    
                    # Type conversion for numeric fields
                    for col in Model.__table__.columns:
                        k = col.name
                        if k in filtered and filtered[k] is not None:
                            try:
                                # For String columns, just strip whitespace
                                if isinstance(col.type, String):
                                    filtered[k] = str(filtered[k]).strip()
                                # For Integer columns, convert to int
                                elif isinstance(col.type, Integer):
                                    filtered[k] = str(int(float(filtered[k])))
                                # For Float columns, convert to float
                                elif isinstance(col.type, Float):
                                    filtered[k] = str(float(filtered[k]))
                            except (ValueError, TypeError):
                                filtered[k] = None
                    
                    # Check if stat already exists
                    if 'season' in filtered and 'team' in filtered:
                        existing = session.query(Model).filter_by(
                            player_id=player_obj.id,
                            season=filtered['season'],
                            team=filtered['team']
                        ).first()
                        if existing:
                            continue
                    
                    stat_obj = Model(**filtered)
                    session.add(stat_obj)
                    stats_found = True
                
                if skip_for_mlb_team:
                    break
            
            if skip_for_mlb_team:
                skipped_mlb += 1
                pbar.set_postfix({'Status': 'Skipped MLB'})
                pbar.update(1)
                continue
            
            # Update player's team based on most recent stats
            if stats_found:
                # Find most recent team from stats
                latest_batting = session.query(StandardBattingStat).filter_by(player_id=player_obj.id).order_by(StandardBattingStat.season.desc()).first()
                latest_pitching = session.query(StandardPitchingStat).filter_by(player_id=player_obj.id).order_by(StandardPitchingStat.season.desc()).first()
                
                if latest_batting and latest_pitching:
                    if latest_batting.season >= latest_pitching.season:
                        player_obj.team = latest_batting.team
                    else:
                        player_obj.team = latest_pitching.team
                elif latest_batting:
                    player_obj.team = latest_batting.team
                elif latest_pitching:
                    player_obj.team = latest_pitching.team
            
            session.commit()
            ingested += 1
            pbar.set_postfix({'Status': f'OK - {player_obj.team}'})
            pbar.update(1)
            
        except Exception as e:
            pbar.set_postfix({'Status': f'Error: {str(e)[:30]}...'})
            pbar.update(1)
            session.rollback()
            errors += 1
    
    pbar.close()
    print(f"\n[SUMMARY] {level} Players:")
    print(f"  Ingested: {ingested}")
    print(f"  Skipped MLB: {skipped_mlb}")
    print(f"  Errors: {errors}")
    
    session.close()

if __name__ == '__main__':
    main() 