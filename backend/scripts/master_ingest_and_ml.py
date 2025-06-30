import subprocess
import sys
import os
from database import SessionLocal
from ml_service import ml_service

def run_script(script_path):
    print(f"[MASTER] Running: {script_path}")
    result = subprocess.run([sys.executable, script_path], check=False)
    if result.returncode != 0:
        print(f"[MASTER] Script failed: {script_path}")
        sys.exit(result.returncode)

if __name__ == '__main__':
    # 1. Ingest MLB data
    run_script(os.path.join('backend', 'scripts', 'ingest_bref_players.py'))
    # 2. Ingest MiLB data (if script exists)
    milb_script = os.path.join('backend', 'etl', 'ingest_milb_prospects.py')
    if os.path.exists(milb_script):
        run_script(milb_script)
    # 3. Run ML normalization
    print("[MASTER] Running ML normalization...")
    db = SessionLocal()
    ml_service.compute_stat_normalization(db)
    db.close()
    print("[MASTER] All ingestion and ML steps complete.") 