import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import models

def empty_canonical_tables():
    db: Session = SessionLocal()
    try:
        tables = [
            models.StandardFieldingStat,
            models.AdvancedPitchingStat,
            models.ValuePitchingStat,
            models.StandardPitchingStat,
            models.AdvancedBattingStat,
            models.ValueBattingStat,
            models.StandardBattingStat,
            models.StatRow,
            models.StatTable,
            models.PlayerBio,
            models.PlayerFeatures,
            models.Player,
        ]
        for table in tables:
            deleted = db.query(table).delete()
            print(f"Deleted {deleted} rows from {table.__tablename__}")
        db.commit()
        print("Canonical tables emptied.")
    finally:
        db.close()

if __name__ == "__main__":
    empty_canonical_tables() 