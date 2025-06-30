from fastapi import APIRouter, BackgroundTasks, Request
import subprocess
import os

router = APIRouter(prefix="/ingest", tags=["ingest"])

# Helper to run a script in the background
def run_script(script_args):
    with open("script_output.log", "a") as f:
        subprocess.Popen(script_args, stdout=f, stderr=f)

@router.post("/mlb-urls")
def scrape_mlb_urls(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_script, ["python", "scripts/scrape_mlb_player_urls.py"])
    return {"status": "Started MLB URL scraping"}

@router.post("/mlb")
def ingest_mlb(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_script, ["python", "scripts/ingest_bref_players.py", "--url_file", "player_url_lists/mlb_player_urls.txt"])
    return {"status": "Started MLB ingestion"}

@router.post("/milb-urls")
def scrape_milb_urls(background_tasks: BackgroundTasks):
    # Run all MiLB URL scraping scripts
    scripts = [
        ["python", "scripts/scrape_aaa_player_urls.py"],
        # Add other MiLB scraping scripts here if needed
    ]
    for script in scripts:
        background_tasks.add_task(run_script, script)
    return {"status": "Started MiLB URL scraping"}

@router.post("/milb")
def ingest_milb(background_tasks: BackgroundTasks):
    # Run all MiLB ingestion scripts for each url file
    url_files = [
        "player_url_lists/aaa_player_urls.txt",
        "player_url_lists/aa_player_urls.txt",
        "player_url_lists/a+_player_urls.txt",
        "player_url_lists/a_player_urls.txt",
        "player_url_lists/rk_player_urls.txt",
    ]
    for url_file in url_files:
        background_tasks.add_task(run_script, ["python", "scripts/ingest_milb_players.py", url_file])
    return {"status": "Started MiLB ingestion"}

@router.post("/clear-db")
def clear_database(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_script, ["python", "scripts/empty_database.py"])
    return {"status": "Started clearing database"}

@router.post("/ml-update")
def update_ml(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_script, ["python", "scripts/master_ingest_and_ml.py"])
    return {"status": "Started ML update"}

@router.post("/debug-ml")
def debug_ml(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_script, ["python", "scripts/debug_ml_service.py"])
    return {"status": "Started ML debug"}

@router.post("/test-level-weights")
def test_level_weights(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_script, ["python", "scripts/test_level_weights.py"])
    return {"status": "Started test level weights"} 