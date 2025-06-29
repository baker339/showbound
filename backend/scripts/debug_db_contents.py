import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import SessionLocal
from backend.models import Player, StandardBattingStat, AdvancedBattingStat, StandardPitchingStat, StandardFieldingStat

def print_table_info(session, model, name):
    count = session.query(model).count()
    print(f"{name}: {count} rows")
    samples = session.query(model).limit(3).all()
    for s in samples:
        print(f"  Sample: {s.__dict__}")

def main():
    session = SessionLocal()
    print_table_info(session, Player, "Players")
    print_table_info(session, StandardBattingStat, "StandardBattingStat")
    print_table_info(session, AdvancedBattingStat, "AdvancedBattingStat")
    print_table_info(session, StandardPitchingStat, "StandardPitchingStat")
    print_table_info(session, StandardFieldingStat, "StandardFieldingStat")
    session.close()

if __name__ == "__main__":
    main() 