#!/usr/bin/env python3

import time
import subprocess
import sys
import os

def main():
    print("⏰ Waiting 1 hour before retrying scraping...")
    print("This will help avoid rate limiting from Baseball Reference.")
    
    # Wait for 1 hour (3600 seconds)
    for i in range(3600, 0, -60):
        minutes = i // 60
        print(f"⏳ {minutes} minutes remaining...")
        time.sleep(60)
    
    print("🚀 Starting scraping script...")
    
    # Run the scraping script
    script_path = os.path.join(os.path.dirname(__file__), 'scrape_mlb_and_milb_player_urls.py')
    result = subprocess.run([sys.executable, script_path], 
                          cwd=os.path.dirname(os.path.dirname(__file__)),
                          env={**os.environ, 'PYTHONPATH': os.path.dirname(os.path.dirname(__file__))})
    
    if result.returncode == 0:
        print("✅ Scraping completed successfully!")
    else:
        print("❌ Scraping failed with exit code:", result.returncode)

if __name__ == "__main__":
    main() 