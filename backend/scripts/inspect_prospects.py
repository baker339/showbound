import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import models
import json

def main():
    db: Session = SessionLocal()
    try:
        prospects = db.query(models.Prospect).limit(20).all()
        for p in prospects:
            stats_summary = p.stats_json if p.stats_json is not None else None
            print(f"id={p.id}, name={p.name}, level={p.level}, stats_json={json.dumps(stats_summary)[:100]}...")
    if not prospects:
            print("No prospects found.")
    finally:
        db.close()

if __name__ == "__main__":
    main() 