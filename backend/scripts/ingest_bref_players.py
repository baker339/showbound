import os
import sys
import requests
from bs4 import BeautifulSoup, Comment, Tag
from sqlalchemy.exc import IntegrityError
import time
import unicodedata
import argparse
from tqdm import tqdm
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import SessionLocal
from models import Player, StandardBattingStat, ValueBattingStat, AdvancedBattingStat, StandardPitchingStat, ValuePitchingStat, AdvancedPitchingStat, StandardFieldingStat, PlayerFeatures
from ml_service import ml_service

# Mapping from Baseball Reference headers to model fields
BREF_TO_MODEL = {
    'batting': {
        'Season': 'season', 'Age': 'age', 'Team': 'team', 'Lg': 'lg', 'WAR': 'war', 'G': 'g', 'PA': 'pa', 'AB': 'ab', 'R': 'r', 'H': 'h', '2B': 'doubles', '3B': 'triples', 'HR': 'hr', 'RBI': 'rbi', 'SB': 'sb', 'CS': 'cs', 'BB': 'bb', 'SO': 'so', 'BA': 'ba', 'OBP': 'obp', 'SLG': 'slg', 'OPS': 'ops', 'OPS+': 'ops_plus', 'ROBA': 'roba', 'RBat+': 'rbat_plus', 'TB': 'tb', 'GIDP': 'gidp', 'HBP': 'hbp', 'SH': 'sh', 'SF': 'sf', 'IBB': 'ibb', 'Pos': 'pos', 'Awards': 'awards'
    },
    'advanced_batting': {
        'Season': 'season',
        'Age': 'age',
        'Team': 'team',
        'Lg': 'lg',
        'PA': 'pa',
        'rOBA': 'roba',
        'Rbat+': 'rbat_plus',
        'BAbip': 'babip',
        'ISO': 'iso',
        'HR%': 'hr_pct',
        'SO%': 'so_pct',
        'BB%': 'bb_pct',
        'EV': 'ev',
        'HardH%': 'hardh_pct',
        'LD%': 'ld_pct',
        'GB%': 'gb_pct',
        'FB%': 'fb_pct',
        'GB/FB': 'gb_fb',
        'Pull%': 'pull_pct',
        'Cent%': 'cent_pct',
        'Oppo%': 'oppo_pct',
        'WPA': 'wpa',
        'cWPA': 'cwpa',
        'RE24': 're24',
        'RS%': 'rs_pct',
        'SB%': 'sb_pct',
        'XBT%': 'xbt_pct',
        'Pos': 'pos',
        'Awards': 'awards',
    },
    'value_batting': {
        'Season': 'season',
        'Age': 'age',
        'Team': 'team',
        'Lg': 'lg',
        'PA': 'pa',
        'Rbat': 'rbat',
        'Rbaser': 'rbaser',
        'Rdp': 'rdp',
        'Rfield': 'rfield',
        'Rpos': 'rpos',
        'RAA': 'raa',
        'WAA': 'waa',
        'Rrep': 'rrep',
        'RAR': 'rar',
        'WAR': 'war',
        'waaWL%': 'waa_wl_pct',
        '162WL%': 'wl_162_pct',
        'oWAR': 'owar',
        'dWAR': 'dwar',
        'oRAR': 'orar',
        'Pos': 'pos',
        'Awards': 'awards',
    },
    'value_pitching': {
        'Season': 'season',
        'Age': 'age',
        'Team': 'team',
        'Lg': 'lg',
        'IP': 'ip',
        'G': 'g',
        'GS': 'gs',
        'R': 'r',
        'RA9': 'ra9',
        'RA9opp': 'ra9_opp',
        'RA9def': 'ra9_def',
        'RA9role': 'ra9_role',
        'RA9extras': 'ra9_extras',
        'PPFp': 'ppfp',
        'RA9avg': 'ra9_avg_pitcher',
        'RAA': 'raa',
        'WAA': 'waa',
        'WAAadj': 'waa_adj',
        'WAR': 'war',
        'RAR': 'rar',
        'waaWL%': 'waa_wl_pct',
        '162WL%': 'wl_162_pct',
        'Awards': 'awards',
    },
    'advanced_pitching': {
        'Season': 'season',
        'Age': 'age',
        'Team': 'team',
        'Lg': 'lg',
        'IP': 'ip',
        'BA': 'ba',
        'OBP': 'obp',
        'SLG': 'slg',
        'OPS': 'ops',
        'BAbip': 'babip',
        'HR%': 'hr_pct',
        'K%': 'k_pct',
        'BB%': 'bb_pct',
        'EV': 'ev',
        'HardH%': 'hardh_pct',
        'LD%': 'ld_pct',
        'GB%': 'gb_pct',
        'FB%': 'fb_pct',
        'GB/FB': 'gb_fb',
        'WPA': 'wpa',
        'cWPA': 'cwpa',
        'RE24': 're24',
        'Awards': 'awards',
    },
    'pitching': {
        'Season': 'season', 'Age': 'age', 'Team': 'team', 'Lg': 'lg', 'W': 'w', 'L': 'l', 'W-L%': 'wl_pct', 'ERA': 'era', 'G': 'g', 'GS': 'gs', 'GF': 'gf', 'CG': 'cg', 'SHO': 'sho', 'SV': 'sv', 'IP': 'ip', 'H': 'h', 'R': 'r', 'ER': 'er', 'HR': 'hr', 'BB': 'bb', 'IBB': 'ibb', 'SO': 'so', 'HBP': 'hbp', 'BK': 'bk', 'WP': 'wp', 'BF': 'bf', 'ERA+': 'era_plus', 'FIP': 'fip', 'WHIP': 'whip', 'H9': 'h9', 'HR9': 'hr9', 'BB9': 'bb9', 'SO9': 'so9', 'SO/W': 'so_w', 'Awards': 'awards'
    },
    'fielding': {
        'Season': 'season',
        'Age': 'age',
        'Team': 'team',
        'Lg': 'lg',
        'Pos': 'pos',
        'G': 'g',
        'GS': 'gs',
        'CG': 'cg',
        'Inn': 'inn',
        'Ch': 'ch',
        'PO': 'po',
        'A': 'a',
        'E': 'e',
        'DP': 'dp',
        'Fld%': 'fld_pct',
        'lgFld%': 'lgfld_pct',
        'Rdrs': 'rdrs',
        'Rdrs/yr': 'rdrs_yr',
        'RF/9': 'rf9',
        'lgRF9': 'lgrf9',
        'RF/G': 'rfg',
        'lgRFG': 'lgrfg',
        'SB': 'sb',
        'CS': 'cs',
        'CS%': 'cs_pct',
        'lgCS%': 'lgcs_pct',
        'Pick': 'pick',
        'Awards': 'awards',
    }
}

# Expanded MLB team normalization mapping: covers all 30 teams, common abbreviations, city names, nicknames, and BRef abbreviations
MLB_TEAM_MAP = {
    # American League East
    'new york yankees': 'Yankees', 'nyy': 'Yankees', 'yankees': 'Yankees',
    'boston red sox': 'Red Sox', 'bos': 'Red Sox', 'red sox': 'Red Sox',
    'toronto blue jays': 'Blue Jays', 'tor': 'Blue Jays', 'blue jays': 'Blue Jays',
    'baltimore orioles': 'Orioles', 'bal': 'Orioles', 'orioles': 'Orioles',
    'tampa bay rays': 'Rays', 'tb': 'Rays', 'tbr': 'Rays', 'rays': 'Rays',
    # American League Central
    'cleveland guardians': 'Guardians', 'cle': 'Guardians', 'clev': 'Guardians', 'guardians': 'Guardians',
    'minnesota twins': 'Twins', 'min': 'Twins', 'twins': 'Twins',
    'chicago white sox': 'White Sox', 'cws': 'White Sox', 'chw': 'White Sox', 'white sox': 'White Sox',
    'detroit tigers': 'Tigers', 'det': 'Tigers', 'tigers': 'Tigers',
    'kansas city royals': 'Royals', 'kc': 'Royals', 'kcr': 'Royals', 'royals': 'Royals',
    # American League West
    'houston astros': 'Astros', 'hou': 'Astros', 'astros': 'Astros',
    'texas rangers': 'Rangers', 'tex': 'Rangers', 'rangers': 'Rangers',
    'seattle mariners': 'Mariners', 'sea': 'Mariners', 'mariners': 'Mariners',
    'oakland athletics': 'Athletics', 'oak': 'Athletics', 'athletics': 'Athletics', "a's": 'Athletics',
    'ath': 'Athletics', 'athl': 'Athletics',
    'los angeles angels': 'Angels', 'laa': 'Angels', 'angels': 'Angels', 'anaheim angels': 'Angels',
    # National League East
    'atlanta braves': 'Braves', 'atl': 'Braves', 'braves': 'Braves',
    'philadelphia phillies': 'Phillies', 'phi': 'Phillies', 'phillies': 'Phillies',
    'new york mets': 'Mets', 'nym': 'Mets', 'mets': 'Mets',
    'miami marlins': 'Marlins', 'mia': 'Marlins', 'marlins': 'Marlins', 'florida marlins': 'Marlins',
    'washington nationals': 'Nationals', 'was': 'Nationals', 'wsn': 'Nationals', 'nationals': 'Nationals', 'montreal expos': 'Nationals',
    # National League Central
    'st. louis cardinals': 'Cardinals', 'st louis cardinals': 'Cardinals', 'stl': 'Cardinals', 'cardinals': 'Cardinals',
    'milwaukee brewers': 'Brewers', 'mil': 'Brewers', 'brewers': 'Brewers',
    'chicago cubs': 'Cubs', 'chc': 'Cubs', 'cubs': 'Cubs',
    'cincinnati reds': 'Reds', 'cin': 'Reds', 'reds': 'Reds',
    'pittsburgh pirates': 'Pirates', 'pit': 'Pirates', 'pirates': 'Pirates',
    # National League West
    'arizona diamondbacks': 'Diamondbacks', 'ari': 'Diamondbacks', 'diamondbacks': 'Diamondbacks', 'dbacks': 'Diamondbacks',
    'los angeles dodgers': 'Dodgers', 'lad': 'Dodgers', 'dodgers': 'Dodgers',
    'san diego padres': 'Padres', 'sd': 'Padres', 'sdg': 'Padres', 'sdp': 'Padres', 'padres': 'Padres',
    'san francisco giants': 'Giants', 'sf': 'Giants', 'sfn': 'Giants', 'sfg': 'Giants', 'giants': 'Giants',
    'colorado rockies': 'Rockies', 'col': 'Rockies', 'rockies': 'Rockies',
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
HEADERS = {"User-Agent": USER_AGENT}

def normalize_team(team_str):
    if not team_str:
        return None
    import re
    team_clean = re.sub(r'\(.*?\)', '', team_str).strip().lower()
    if team_clean.startswith('the '):
        team_clean = team_clean[4:]
    mapped = MLB_TEAM_MAP.get(team_clean)
    return mapped or team_clean.title()

def get_soup(url):
    time.sleep(3)  # 3 second delay before each request
    try:
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, 'html.parser')
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print(f"Rate limited (429) on {url}. Stopping script.")
            sys.exit(1)
        else:
            raise

def extract_table(soup, table_id):
    table = soup.find('table', id=table_id)
    if not table:
        return None, None
    thead = table.find('thead')
    headers = [th.get_text(strip=True) for th in thead.find_all('th')]
    tbody = table.find('tbody')
    rows = []
    for tr in tbody.find_all('tr'):
        # Skip divider/header/aggregate rows
        if tr.get('class') and ('over_header' in tr.get('class') or 'thead' in tr.get('class')):
            continue
        row = [td.get_text(strip=True) for td in tr.find_all(['th', 'td'])]
        # Skip rows that don't match header length (likely divider/aggregate)
        if not row or len(row) < len(headers) // 2:  # allow for some missing data but not too short
            continue
        rows.append(row)
    return headers, rows

def parse_and_insert_stat(session, player_obj, table_type, headers, rows, Model):
    # Determine mapping type and canonical header start
    if 'batting' in table_type:
        mapping = BREF_TO_MODEL['batting']
        unique_keys = ['player_id', 'season', 'team']
        canonical_start = 'Season'
    elif 'pitching' in table_type:
        mapping = BREF_TO_MODEL['pitching']
        unique_keys = ['player_id', 'season', 'team']
        canonical_start = 'Season'
    elif 'fielding' in table_type:
        mapping = BREF_TO_MODEL['fielding']
        unique_keys = ['player_id', 'season', 'team', 'pos']
        canonical_start = 'Season'
    else:
        mapping = {}
        unique_keys = ['player_id']
        canonical_start = None
    for row in rows:
        # Align headers and row to canonical start
        if canonical_start and canonical_start in headers:
            idx = headers.index(canonical_start)
            use_headers = headers[idx:]
            use_row = row[idx:]
        else:
            use_headers = headers
            use_row = row
        # if 'fielding' in table_type:
        #     print(f"[DEBUG] Fielding headers: {use_headers}")
        #     print(f"[DEBUG] Fielding row: {use_row}")
        data = dict(zip(use_headers, use_row))
        # Map Baseball Reference headers to model fields
        data = {mapping.get(k, k): v for k, v in data.items()}
        data['player_id'] = player_obj.id
        # Normalize team field if present
        if 'team' in data and data['team']:
            data['team'] = normalize_team(data['team'])
        # Robust row validation for fielding (and all stat tables)
        season = data.get('season')
        team = data.get('team')
        pos = data.get('pos')
        # Only skip if season, team, or pos is missing/empty, or pos is 'total' (case-insensitive)
        if not season or not season.isdigit() or len(season) != 4:
            continue
        if not team:
            continue
        if pos is None or pos.strip() == '' or pos.strip().lower() == 'total':
            continue
        # Skip aggregate/combined team rows (e.g., 2Tm, 3Tm, 4Tm, TOT, TOTAL, 2Tms, 3Tms, etc.)
        import re
        raw_team = data.get('team') if 'team' in data else None
        if raw_team is not None and (re.match(r'^[0-9]+TMS?$', str(raw_team).strip().upper()) or str(raw_team).strip().upper() in ['TOT', 'TOTAL']):
            continue
        # Only pass valid model fields
        valid_fields = set(str(c.name) for c in Model.__table__.columns)
        filtered_data = {str(k): (v if v != '' else None) for k, v in data.items() if str(k) in valid_fields}
        # Cast values to correct type based on model definition
        for col in Model.__table__.columns:
            k = col.name
            value = filtered_data.get(k, None)
            if value is not None:
                try:
                    if isinstance(col.type.python_type, type):
                        typ = col.type.python_type
                    else:
                        typ = type(col.type.python_type)
                    if typ is int:
                        filtered_data[k] = int(float(value))
                    elif typ is float:
                        filtered_data[k] = float(value)
                    elif typ is str:
                        filtered_data[k] = str(value).strip()
                except Exception:
                    pass
        # Normalize unique key fields for duplicate checking
        filter_kwargs = {}
        for k in unique_keys:
            v = filtered_data.get(k)
            if v is None:
                filter_kwargs[k] = None
            else:
                filter_kwargs[k] = str(v).strip()
        exists = session.query(Model).filter_by(**filter_kwargs).first()
        if exists:
            continue  # Skip duplicate
        stat_obj = Model(**filtered_data)
        session.add(stat_obj)

def extract_bio_from_meta(soup):
    bio = {}
    meta_div = soup.find('div', id='meta')
    if not meta_div:
        return bio
    # Extract player image
    media_div = meta_div.find('div', class_='media-item')
    if media_div:
        img = media_div.find('img')
        if img and img.has_attr('src'):
            bio['image_url'] = img['src']
    for p in meta_div.find_all('p'):
        strong = p.find('strong')
        if strong:
            label = strong.get_text(strip=True).replace(':', '')
            # Special handling for Team (may have <a> and parenthetical)
            if 'Team' in label:
                team_a = p.find('a')
                team_text = team_a.get_text(strip=True) if team_a else p.get_text(strip=True).replace(strong.get_text(strip=True), '').strip(': ').strip()
                bio['team'] = normalize_team(team_text)
            # Special handling for Bats/Throws
            elif 'Bats' in label or 'Throws' in label:
                text = p.get_text(' ', strip=True)
                bats = throws = None
                if 'Bats:' in text and 'Throws:' in text:
                    parts = text.split('•')
                    for part in parts:
                        if 'Bats:' in part:
                            bats = part.replace('Bats:', '').strip()
                        if 'Throws:' in part:
                            throws = part.replace('Throws:', '').strip()
                bio['bats'] = bats
                bio['throws'] = throws
            # Special handling for Height/Weight
            elif 'lb' in p.get_text() and '(' in p.get_text():
                # e.g., '5-6, 167lb (168cm, 75kg)'
                text = p.get_text(' ', strip=True)
                import re
                height_match = re.search(r'(\d+-\d+)', text)
                weight_match = re.search(r'(\d+)lb', text)
                if height_match:
                    bio['height'] = height_match.group(1)
                if weight_match:
                    bio['weight'] = weight_match.group(1)
            # Special handling for Born/Birth Date
            elif 'Born' in label:
                birth_span = p.find('span', {'id': 'necro-birth'})
                if birth_span and birth_span.has_attr('data-birth'):
                    bio['birth_date'] = birth_span['data-birth']
                else:
                    # Fallback: try to extract from text
                    import re
                    text = p.get_text(' ', strip=True)
                    date_match = re.search(r'(\w+ \d{1,2}, \d{4})', text)
                    if date_match:
                        bio['birth_date'] = date_match.group(1)
            # Special handling for Position
            elif 'Position' in label:
                pos = p.get_text(strip=True).replace(strong.get_text(strip=True), '').strip(': ').strip()
                bio['primary_position'] = pos
            # Special handling for Full Name
            elif 'Full Name' in label:
                full_name = p.get_text(strip=True).replace(strong.get_text(strip=True), '').strip(': ').strip()
                bio['full_name'] = full_name
            else:
                # Generic: store label and value
                value = p.get_text(strip=True).replace(strong.get_text(strip=True), '').strip(': ').strip()
                bio[label.lower().replace(' ', '_')] = value
        else:
            # Handle height/weight if not in <strong>
            text = p.get_text(' ', strip=True)
            if 'lb' in text and '(' in text:
                import re
                height_match = re.search(r'(\d+-\d+)', text)
                weight_match = re.search(r'(\d+)lb', text)
                if height_match:
                    bio['height'] = height_match.group(1)
                if weight_match:
                    bio['weight'] = weight_match.group(1)
    return bio

# Robust stat table extraction
STAT_TABLE_IDS = [
    ('players_standard_batting', StandardBattingStat),
    ('players_value_batting', ValueBattingStat),
    ('players_advanced_batting', AdvancedBattingStat),
    ('players_standard_pitching', StandardPitchingStat),
    ('players_value_pitching', ValuePitchingStat),
    ('players_advanced_pitching', AdvancedPitchingStat),
    ('players_standard_fielding', StandardFieldingStat),
]

def extract_and_insert_stat_tables(soup, player_obj, session):
    found_any = False
    all_stat_rows = []  # Collect all valid stat rows in memory
    candidate_stat_rows = []
    dom_tables = {table_id: soup.find('table', id=table_id) for table_id, _ in STAT_TABLE_IDS}
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        if '<table' in comment:
            comment_soup = BeautifulSoup(comment, 'html.parser')
            for table_id, _ in STAT_TABLE_IDS:
                if dom_tables[table_id] is None:
                    table = comment_soup.find('table', id=table_id)
                    if table:
                        dom_tables[table_id] = table
    for (table_id, Model) in STAT_TABLE_IDS:
        table = dom_tables[table_id]
        if not table:
            continue
        thead = table.find('thead')
        headers = [th.get_text(strip=True) for th in thead.find_all('th')]
        tbody = table.find('tbody')
        for tr in tbody.find_all('tr'):
            if tr.get('class') and ('over_header' in tr.get('class') or 'thead' in tr.get('class')):
                continue
            row = [td.get_text(strip=True) for td in tr.find_all(['th', 'td'])]
            if not row or len(row) < len(headers) // 2:
                continue
            if 'Season' in headers:
                idx = headers.index('Season')
                use_headers = headers[idx:]
                if len(row) >= len(use_headers):
                    use_row = row[-len(use_headers):]
                else:
                    continue
            else:
                use_headers = headers
                use_row = row
            mapping = None
            if 'batting' in table_id:
                if 'advanced' in table_id:
                    mapping = BREF_TO_MODEL['advanced_batting']
                elif 'value' in table_id:
                    mapping = BREF_TO_MODEL['value_batting']
                else:
                    mapping = BREF_TO_MODEL['batting']
            elif 'pitching' in table_id:
                if 'advanced' in table_id:
                    mapping = BREF_TO_MODEL['advanced_pitching']
                elif 'value' in table_id:
                    mapping = BREF_TO_MODEL['value_pitching']
                else:
                    mapping = BREF_TO_MODEL['pitching']
            elif 'fielding' in table_id:
                mapping = BREF_TO_MODEL['fielding']
            else:
                mapping = {}
            data = dict(zip(use_headers, use_row))
            data = {mapping.get(k, k): v for k, v in data.items()}
            data['player_id'] = player_obj.id
            if 'team' in data and data['team']:
                data['team'] = normalize_team(data['team'])
            season = data.get('season')
            team = data.get('team')
            pos = data.get('pos')
            if not season or not season.isdigit() or len(season) != 4:
                continue
            if not team:
                continue
            if table_id == 'players_standard_fielding':
                if pos is None or pos.strip() == '' or pos.strip().lower() == 'total':
                    continue
            # Skip aggregate/combined team rows (e.g., 2Tm, 3Tm, 4Tm, TOT, TOTAL, 2TMS, 3TMS, etc.)
            import re
            raw_team = data.get('team') if 'team' in data else None
            if raw_team is not None and (re.match(r'^[0-9]+TMS?$', str(raw_team).strip().upper()) or str(raw_team).strip().upper() in ['TOT', 'TOTAL']):
                continue
            # Only normalize if not aggregate
            if 'team' in data and data['team']:
                data['team'] = normalize_team(data['team'])
            valid_fields = set(str(c.name) for c in Model.__table__.columns)
            filtered_data = {str(k): (v if v != '' else None) for k, v in data.items() if str(k) in valid_fields}
            for col in Model.__table__.columns:
                k = col.name
                value = filtered_data.get(k, None)
                if value is not None:
                    try:
                        if isinstance(col.type.python_type, type):
                            typ = col.type.python_type
                        else:
                            typ = type(col.type.python_type)
                        if typ is int:
                            filtered_data[k] = int(float(value))
                        elif typ is float:
                            filtered_data[k] = float(value)
                        elif typ is str:
                            filtered_data[k] = str(value).strip()
                    except Exception:
                        pass
            if 'batting' in table_id or 'pitching' in table_id:
                unique_keys = ['player_id', 'season', 'team']
            elif 'fielding' in table_id:
                unique_keys = ['player_id', 'season', 'team', 'pos']
            else:
                unique_keys = ['player_id']
            filter_kwargs = {}
            for k in unique_keys:
                v = filtered_data.get(k)
                if v is None:
                    filter_kwargs[k] = None
                else:
                    filter_kwargs[k] = str(v).strip()
            exists = session.query(Model).filter_by(**filter_kwargs).first()
            if exists:
                continue
            stat_obj = Model(**filtered_data)
            session.add(stat_obj)
            # For team assignment and stat display
            stat_row = {'season': int(season), 'team': team, 'table': table_id, 'g': int(data.get('g', 0) or 0), 'pa': int(data.get('pa', 0) or 0), 'ip': float(data.get('ip', 0) or 0)}
            candidate_stat_rows.append(stat_row)
            all_stat_rows.append({**data, 'table': table_id})
            found_any = True
    # --- Team assignment logic ---
    if candidate_stat_rows:
        # Deduplicate by (season, team, table)
        seen = set()
        deduped = []
        for row in candidate_stat_rows:
            key = (row['season'], row['team'], row['table'])
            if key not in seen:
                deduped.append(row)
                seen.add(key)
        deduped.sort(key=lambda r: r['season'], reverse=True)
        latest_season = deduped[0]['season']
        latest_rows = [r for r in deduped if r['season'] == latest_season]
        def row_sort_key(r):
            # Use regex to match any nTm, nTms, etc. on the raw team string
            import re
            raw_team = r['team']
            is_aggregate = bool(re.match(r'^[0-9]+TMS?$', str(raw_team).strip().upper()) or str(raw_team).strip().upper() in ['TOT', 'TOTAL'])
            return (
                0 if not is_aggregate else 1,
                -(r.get('g', 0) or 0),
                -(r.get('pa', 0) or 0),
                -(r.get('ip', 0) or 0)
            )
        latest_rows.sort(key=row_sort_key)
        chosen = latest_rows[0]
        player_obj.team = chosen['team']
    elif all_stat_rows:
        player_obj.team = 'UNKNOWN'
    else:
        player_obj.team = 'NO_TEAM'
    player_obj.level = 'MLB'
    session.add(player_obj)
    session.commit()
    # --- Stat display: sort all_stat_rows by season ascending, team ---
    all_stat_rows.sort(key=lambda r: (int(r.get('season', 0)), r.get('team', '')))
    return all_stat_rows

def extract_minor_league_stats(soup, player_obj, session):
    """Extract minor league stats from register page and add to existing player"""
    # Look for "Minor Lg Stats" link
    minor_lg_link = soup.find('a', text='Minor Lg Stats')
    if not minor_lg_link:
        return False
    
    minor_lg_url = 'https://www.baseball-reference.com' + minor_lg_link['href']
    
    try:
        # Get the minor league page
        minor_soup = get_soup(minor_lg_url)
        
        # Use the same logic as MiLB ingestion for register pages
        stats_found = False
        
        # Mapping for register pages (same as MiLB script)
        BATTING_MAP = {
            'Year': 'season', 'Tm': 'team', 'Lev': 'level', 'G': 'g', 'PA': 'pa', 'AB': 'ab', 'R': 'r', 'H': 'h', '2B': 'doubles', '3B': 'triples', 'HR': 'hr', 'RBI': 'rbi', 'SB': 'sb', 'CS': 'cs', 'BB': 'bb', 'SO': 'so', 'BA': 'ba', 'OBP': 'obp', 'SLG': 'slg', 'OPS': 'ops', 'TB': 'tb', 'GDP': 'gidp', 'HBP': 'hbp', 'SH': 'sh', 'SF': 'sf', 'IBB': 'ibb', 'Age': 'age', 'Lg': 'lg', 'Aff': 'aff',
        }
        PITCHING_MAP = {
            'Year': 'season', 'Tm': 'team', 'Lev': 'level', 'W': 'w', 'L': 'l', 'W-L%': 'wl_pct', 'ERA': 'era', 'G': 'g', 'GS': 'gs', 'GF': 'gf', 'CG': 'cg', 'SHO': 'sho', 'SV': 'sv', 'IP': 'ip', 'H': 'h', 'R': 'r', 'ER': 'er', 'HR': 'hr', 'BB': 'bb', 'IBB': 'ibb', 'SO': 'so', 'HBP': 'hbp', 'BK': 'bk', 'WP': 'wp', 'BF': 'bf', 'ERA+': 'era_plus', 'FIP': 'fip', 'WHIP': 'whip', 'H9': 'h9', 'HR9': 'hr9', 'BB9': 'bb9', 'SO9': 'so9', 'SO/W': 'so_w', 'Age': 'age', 'Lg': 'lg', 'Aff': 'aff',
        }
        FIELDING_MAP = {
            'Year': 'season', 'Tm': 'team', 'Lev': 'level', 'Pos': 'pos', 'G': 'g', 'GS': 'gs', 'Inn': 'inn', 'Ch': 'ch', 'PO': 'po', 'A': 'a', 'E': 'e', 'DP': 'dp', 'Fld%': 'fld_pct', 'Rdrs': 'rdrs', 'RF/9': 'rf9', 'SB': 'sb', 'CS': 'cs', 'Age': 'age', 'Lg': 'lg', 'Aff': 'aff',
        }
        
        # Parse stat tables using register page table IDs
        for table_id, Model, MAP in [
            ('standard_batting', StandardBattingStat, BATTING_MAP),
            ('standard_pitching', StandardPitchingStat, PITCHING_MAP),
            ('standard_fielding', StandardFieldingStat, FIELDING_MAP)
        ]:
            table = minor_soup.find('table', id=table_id)
            if not table:
                continue
            
            # Find the header row that contains the actual column names
            header_row = None
            for row in table.find_all('tr'):
                if not isinstance(row, Tag):
                    continue
                cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                if 'Year' in cells and 'Tm' in cells:
                    header_row = cells
                    break
            
            if not header_row:
                continue
            
            # Process data rows
            for row in table.find_all('tr'):
                if not isinstance(row, Tag):
                    continue
                
                cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                if len(cells) != len(header_row):
                    continue
                
                # Skip header rows
                if cells[0] == 'Year' or not cells[0].isdigit():
                    continue
                
                data = dict(zip(header_row, cells))
                
                # Skip aggregate rows
                if 'Tm' in data and ('Teams' in data['Tm'] or 'Lgs' in data['Tm']):
                    continue
                
                # Use 'Lev' for level, 'Tm' for team
                row_level = data.get('Lev')
                team = data.get('Tm')
                season = data.get('Year')
                
                if not (row_level and team and season):
                    continue
                
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
        
        return stats_found
            
    except Exception as e:
        return False

def main():
    parser = argparse.ArgumentParser(description="Ingest BRef player pages into canonical DB.")
    parser.add_argument('--url_file', type=str, default='player_url_lists/mlb_40man_player_urls.txt', help='Path to player URLs file (MLB 40-man)')
    parser.add_argument('--level', type=str, default=None, help='Override level for all players (e.g., AAA)')
    parser.add_argument('--resume', action='store_true', help='Resume: skip players already in DB (by bref_id)')
    args = parser.parse_args()
    url_file = args.url_file
    override_level = args.level
    resume = args.resume
    session = SessionLocal()
    
    # Read URLs
    with open(url_file, 'r') as f:
        player_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    # If resume, get all bref_ids already in the DB
    existing_bref_ids = set()
    if resume:
        existing_bref_ids = set(row[0] for row in session.query(Player.bref_id).filter(Player.bref_id != None).all())
        print(f"[RESUME] Found {len(existing_bref_ids)} players in DB. Will skip these.")

    # Helper to extract bref_id from URL
    def extract_bref_id(url):
        # e.g. https://www.baseball-reference.com/players/x/xxxxxxx.shtml
        import re
        m = re.search(r'/players/[a-z]/([a-z0-9]+)\.shtml', url)
        return m.group(1) if m else None

    # Create progress bar
    pbar = tqdm(total=len(player_urls), desc="Processing MLB players")
    
    ingested = 0
    errors = 0
    
    for url in player_urls:
        bref_id = extract_bref_id(url)
        if resume and bref_id and bref_id in existing_bref_ids:
            pbar.set_postfix({'Status': f'SKIP (already in DB)'})
            pbar.update(1)
            continue
        try:
            soup = get_soup(url)
            # Extract player name from <h1> tag
            name_tag = soup.find('h1')
            full_name = name_tag.get_text(strip=True) if name_tag else None
            if full_name:
                full_name = unicodedata.normalize('NFKC', full_name)
            # Extract bio from meta
            bio = extract_bio_from_meta(soup)
            if not full_name:
                pbar.set_postfix({'Status': 'No name found'})
                pbar.update(1)
                time.sleep(3)
                continue
            
            player_obj = session.query(Player).filter_by(full_name=full_name).first()
            if not player_obj:
                player_obj = Player(
                    full_name=full_name,
                    bref_id=bref_id,
                    birth_date=bio.get('birth_date'),
                    primary_position=bio.get('primary_position'),
                    bats=bio.get('bats'),
                    throws=bio.get('throws'),
                    height=bio.get('height'),
                    weight=bio.get('weight'),
                    image_url=bio.get('image_url'),
                    source_url=url
                )
                session.add(player_obj)
                session.flush()
            else:
                # Patch: always set bref_id if missing
                if bref_id and not getattr(player_obj, 'bref_id', None):
                    setattr(player_obj, 'bref_id', bref_id)
                    session.add(player_obj)
                    session.commit()
            
            stat_rows = extract_and_insert_stat_tables(soup, player_obj, session)
            
            # Try to extract minor league stats
            minor_stats_found = extract_minor_league_stats(soup, player_obj, session)
            
            # --- PATCH: assign team from in-memory stat rows ---
            if stat_rows:
                latest = max(stat_rows, key=lambda r: r['season'])
                player_obj.team = latest['team']  # type: ignore
            else:
                player_obj.team = 'NO_TEAM'  # type: ignore
            
            player_obj.level = 'MLB'  # type: ignore
            session.add(player_obj)
            session.commit()
            
            if override_level:
                player_obj.level = override_level
            
            ingested += 1
            pbar.set_postfix({'Status': f'OK - {player_obj.team}'})
            pbar.update(1)
            time.sleep(3)
            
        except Exception as e:
            pbar.set_postfix({'Status': f'Error: {str(e)[:30]}...'})
            pbar.update(1)
            session.rollback()
            errors += 1
            time.sleep(3)
    
    pbar.close()
    print(f"\n[SUMMARY] MLB Players:")
    print(f"  Ingested: {ingested}")
    print(f"  Errors: {errors}")
    
    session.close()

    # --- Compute and store features for all players ---
    session = SessionLocal()
    players = session.query(Player).all()
    for player in players:
        player_id = getattr(player, 'id', None)
        if not isinstance(player_id, int):
            print(f"[WARN] Skipping player with invalid id: {player_id} ({type(player_id)})")
            continue
        feats = ml_service.extract_player_features(session, player_id)
        if feats is None:
            continue
        # Upsert PlayerFeatures
        pf = session.query(PlayerFeatures).filter_by(player_id=player_id).first()
        if pf:
            pf.raw_features = feats['raw']
            pf.normalized_features = feats['normalized']
        else:
            pf = PlayerFeatures(
                player_id=player_id,
                raw_features=feats['raw'],
                normalized_features=feats['normalized']
            )
            session.add(pf)
    session.commit()
    # Refresh in-memory feature cache after updating DB
    ml_service.refresh_feature_cache(session)

    # --- Compute and store ML level weights ---
    ml_service.compute_level_weights_from_data(session, force=True)
    ml_service.store_level_weights(session)
    print("[ML] Level weights computed and stored.")
    session.close()

if __name__ == '__main__':
    main() 