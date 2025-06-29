import json
import os
import sys
import re
from sqlalchemy.exc import IntegrityError
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import SessionLocal
from backend.models import Player, PlayerBio, StatTable, StatRow, parse_positions

def parse_bats_throws(bats_throws_str):
    # Example: 'Right \u2022Throws:Right' or 'Left \u2022Throws:Left'
    if not bats_throws_str:
        return None, None
    parts = bats_throws_str.split('\u2022')
    bats = None
    throws = None
    if len(parts) == 2:
        bats = parts[0].replace('Bats:', '').strip()
        throws = parts[1].replace('Throws:', '').strip()
    elif len(parts) == 1:
        if 'Throws:' in parts[0]:
            throws = parts[0].replace('Throws:', '').strip()
        else:
            bats = parts[0].replace('Bats:', '').strip()
    return bats, throws

def parse_height_weight(hw_str):
    # Example: '5-10,180lb(178cm, 81kg)'
    if not hw_str:
        return None, None
    match = re.match(r"(\d+-\d+),?(\d+)lb", hw_str)
    if match:
        height = match.group(1)
        weight = match.group(2)
        return height, weight
    return None, None

def get_table_type(caption):
    if not caption:
        return None
    c = caption.lower()
    if 'batting' in c:
        return 'batting'
    if 'pitching' in c:
        return 'pitching'
    if 'fielding' in c:
        return 'fielding'
    return None

IRRELEVANT_TABLES = [
    'Partial Bowling Record Table',
    # Add more irrelevant captions as needed
]

# Canonical header mapping (expand as needed)
HEADER_MAP = {
    'HR': 'home_runs',
    'BA': 'batting_avg',
    'AVG': 'batting_avg',
    'G': 'games',
    'AB': 'at_bats',
    'H': 'hits',
    'R': 'runs',
    '2B': 'doubles',
    '3B': 'triples',
    'RBI': 'rbi',
    'SB': 'stolen_bases',
    'CS': 'caught_stealing',
    'BB': 'walks',
    'SO': 'strikeouts',
    'OBP': 'on_base_pct',
    'SLG': 'slugging_pct',
    'OPS': 'ops',
    'IP': 'innings_pitched',
    'W': 'wins',
    'L': 'losses',
    'ERA': 'era',
    # Add more as needed
}

def canonicalize_row(headers, row):
    d = {}
    for i, h in enumerate(headers):
        key = HEADER_MAP.get(h.strip(), h.strip())
        if i < len(row):
            d[key] = row[i]
        else:
            d[key] = None
    return d

def main():
    session = SessionLocal()
    data_path = os.path.join(os.path.dirname(__file__), '../scraped_players.json')
    with open(data_path, 'r') as f:
        players_data = json.load(f)

    for player in players_data:
        try:
            bio = player.get('bio', {})
            full_name = bio.get('Full Name:')
            birth_date = bio.get('Born:')
            debut_date = bio.get('Debut:')
            positions_raw = bio.get('Positions:')
            positions = parse_positions(positions_raw)
            bats_throws_str = bio.get('Bats:')
            bats, throws = parse_bats_throws(bats_throws_str)
            height_weight_str = None
            for k in bio:
                if 'lb' in k and '(' in k:
                    height_weight_str = k
                    break
            height, weight = parse_height_weight(height_weight_str)
            team = bio.get('Team:')
            source_url = player.get('source_url')

            # Check for existing player (by name + birth_date)
            existing = session.query(Player).filter_by(full_name=full_name, birth_date=birth_date).first()
            if existing:
                print(f"[SKIP] Player already exists: {full_name} ({birth_date})")
                player_obj = existing
                # Update debut_date if missing
                if not getattr(player_obj, "debut_date", None) and debut_date:
                    player_obj.debut_date = debut_date
                    session.add(player_obj)
            else:
                player_obj = Player(
                    full_name=full_name,
                    birth_date=birth_date,
                    debut_date=debut_date,
                    primary_position=positions[0] if positions else None,
                    positions_raw=positions_raw,
                    positions=positions,
                    bats=bats,
                    throws=throws,
                    height=height,
                    weight=weight,
                    team=team,
                    source_url=source_url
                )
                session.add(player_obj)
                session.flush()  # Assigns ID
                print(f"[ADD] Player: {full_name} ({birth_date})")

            # Add all bio fields to PlayerBio
            for field, value in bio.items():
                if not value:
                    continue
                # Avoid duplicate canonical fields
                if field in ['Positions:', 'Bats:', 'Full Name:', 'Born:', 'Team:']:
                    continue
                exists = session.query(PlayerBio).filter_by(player_id=player_obj.id, field_name=field, field_value=value).first()
                if not exists:
                    session.add(PlayerBio(player_id=player_obj.id, field_name=field, field_value=value, source_url=source_url))

            # Merge and deduplicate stat tables by type, parse rows
            tables_by_type = {}
            headers_by_type = {}
            for table in player.get('tables', []):
                caption = table.get('caption')
                if not caption or caption in IRRELEVANT_TABLES:
                    continue
                table_type = get_table_type(caption)
                if not table_type:
                    continue  # skip tables that don't map to a canonical type
                headers = table.get('headers', [])
                if table_type not in tables_by_type:
                    tables_by_type[table_type] = []
                    headers_by_type[table_type] = headers
                # Parse each row as a dict with canonical keys
                for row in table.get('rows', []):
                    parsed = canonicalize_row(headers, row)
                    tables_by_type[table_type].append(parsed)
            # Deduplicate by (year, team)
            for table_type, rows in tables_by_type.items():
                deduped = {}
                for row in rows:
                    year = row.get('year') or row.get('Season') or row.get('season')
                    team = row.get('team') or row.get('Team') or row.get('Tm')
                    key = (str(year).strip() if year else None, str(team).strip() if team else None)
                    if key[0] is None and key[1] is None:
                        # If both year and team are missing, use row index as fallback
                        key = (None, None, len(deduped))
                    if key not in deduped:
                        deduped[key] = row
                stat_table = StatTable(player_id=player_obj.id, caption=table_type.capitalize() + ' Table', table_type=table_type, source_url=source_url)
                session.add(stat_table)
                session.flush()  # Assigns ID
                for idx, row in enumerate(deduped.values()):
                    session.add(StatRow(stat_table_id=stat_table.id, row_index=idx, row_data=row))
                print(f"[TABLE] Player: {full_name} ({birth_date}) - {table_type} rows: {len(rows)} (parsed), {len(deduped)} unique (year, team)")

            session.commit()
        except IntegrityError as e:
            print(f"[ERROR] IntegrityError for {full_name}: {e}")
            session.rollback()
        except Exception as e:
            print(f"[ERROR] Exception for {full_name}: {e}")
            session.rollback()
    session.close()

if __name__ == '__main__':
    main() 