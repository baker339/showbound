import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import SessionLocal
from backend.models import StatTable, StatRow, Player

IRRELEVANT_TABLES = [
    'Partial Bowling Record Table',
    # Add more irrelevant captions as needed
]

def main():
    session = SessionLocal()
    # 1. Remove tables with table_type is NULL or irrelevant caption
    tables_to_delete = session.query(StatTable).filter(
        (StatTable.table_type == None) | (StatTable.caption.in_(IRRELEVANT_TABLES))
    ).all()
    print(f"Deleting {len(tables_to_delete)} tables with NULL table_type or irrelevant caption...")
    for t in tables_to_delete:
        session.query(StatRow).filter(StatRow.stat_table_id == t.id).delete()
        session.delete(t)
    session.commit()

    # 2. For each player and table_type, keep only the most recent StatTable (by id)
    players = session.query(Player.id).all()
    for (player_id,) in players:
        tables = session.query(StatTable).filter(StatTable.player_id == player_id, StatTable.table_type != None).all()
        by_type = {}
        for t in tables:
            by_type.setdefault(t.table_type, []).append(t)
        for table_type, tlist in by_type.items():
            if len(tlist) > 1:
                # Keep the one with the highest id (most recent)
                tlist_sorted = sorted(tlist, key=lambda x: x.id, reverse=True)
                to_keep = tlist_sorted[0]
                to_delete = tlist_sorted[1:]
                print(f"Player {player_id} table_type {table_type}: keeping {to_keep.id}, deleting {[t.id for t in to_delete]}")
                for t in to_delete:
                    session.query(StatRow).filter(StatRow.stat_table_id == t.id).delete()
                    session.delete(t)
    session.commit()
    print("Cleanup complete.")

if __name__ == '__main__':
    main() 