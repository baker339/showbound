import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import SessionLocal
from backend.models import StatTable, StatRow
import json

def main():
    session = SessionLocal()
    tables = session.query(StatTable).all()
    for table in tables:
        rows = session.query(StatRow).filter(StatRow.stat_table_id == table.id).all()
        seen = {}
        to_delete = []
        for row in rows:
            data = row.row_data
            year = data.get('year') or data.get('Season') or data.get('season')
            team = data.get('team') or data.get('Team') or data.get('Tm')
            key = (str(year).strip() if year else None, str(team).strip() if team else None)
            if key[0] is None and key[1] is None:
                key = (None, None, len(seen))
            if key not in seen:
                seen[key] = row
            else:
                to_delete.append(row)
        if to_delete:
            print(f"StatTable {table.id} ({table.caption}, {table.table_type}): deleting {len(to_delete)} duplicate rows")
            for row in to_delete:
                session.delete(row)
    session.commit()
    print("StatRow deduplication complete.")

if __name__ == '__main__':
    main() 