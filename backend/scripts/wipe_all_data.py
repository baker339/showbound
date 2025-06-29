import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import models

def wipe_all():
    db: Session = SessionLocal()
    try:
        # Order matters due to FKs
        tables = [
            models.PlayerGameGrade,
            models.Pitch,
            models.AtBat,
            models.Game,
            models.PlayerRatings,
            models.PlayerAdvancedStats,
            models.PlayerComparison,
            models.PlayerDevelopmentTimeline,
            models.PlayerDevelopmentProjection,
            models.ScoutingReport,
            models.HSPlayerSeason,
            models.NCAAPlayerSeason,
            models.MiLBPlayerSeason,
            models.MLBPlayerSeason,
            models.DraftPick,
            models.Prospect,
            models.Player,
            models.MiLBTeam,
            models.NCAATeam,
            models.HSTeam,
            models.Team,
        ]
        for table in tables:
            deleted = db.query(table).delete()
            print(f"Deleted {deleted} rows from {table.__tablename__}")
        db.commit()
        print("All relevant tables wiped.")
    finally:
        db.close()

if __name__ == "__main__":
    wipe_all() 