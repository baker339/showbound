import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import SessionLocal
from backend.models import StatTable, StatRow

def main():
    session = SessionLocal()
    print("Deleting all StatRow entries...")
    deleted_rows = session.query(StatRow).delete()
    print(f"Deleted {deleted_rows} StatRow entries.")
    print("Deleting all StatTable entries...")
    deleted_tables = session.query(StatTable).delete()
    print(f"Deleted {deleted_tables} StatTable entries.")
    session.commit()
    print("Wipe complete.")

if __name__ == '__main__':
    main() 