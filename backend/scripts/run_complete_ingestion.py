#!/usr/bin/env python3

import os
import sys
import time
import subprocess
import signal
from datetime import datetime, timedelta

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
TIMEOUT_HOURS = 9
PLAYER_URL_DIR = os.path.join(os.path.dirname(__file__), '../player_url_lists')
REQUIRED_FILES = [
    'mlb_player_urls.txt',
    'aaa_player_urls.txt', 
    'aa_player_urls.txt',
    'a+_player_urls.txt',
    'a_player_urls.txt',
    'rk_player_urls.txt'
]

def check_files_exist():
    """Check that all required URL files exist and have content"""
    print("🔍 Checking for required player URL files...")
    
    if not os.path.exists(PLAYER_URL_DIR):
        print(f"❌ Player URL directory not found: {PLAYER_URL_DIR}")
        print("   Waiting for URL scraping to complete...")
        return False
    
    missing_files = []
    empty_files = []
    
    for filename in REQUIRED_FILES:
        filepath = os.path.join(PLAYER_URL_DIR, filename)
        
        if not os.path.exists(filepath):
            missing_files.append(filename)
        else:
            # Check if file has content
            with open(filepath, 'r') as f:
                lines = [line.strip() for line in f if line.strip()]
                if not lines:
                    empty_files.append(filename)
                else:
                    print(f"✅ {filename}: {len(lines)} URLs")
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    if empty_files:
        print(f"⚠️  Empty files: {empty_files}")
        return False
    
    print("✅ All required files found and have content!")
    return True

def run_script_with_timeout(script_path, args, timeout_seconds, description):
    """Run a script with timeout and error handling"""
    print(f"\n🚀 {description}")
    print(f"   Command: python {script_path} {' '.join(args)}")
    print(f"   Timeout: {timeout_seconds} seconds")
    
    start_time = datetime.now()
    
    try:
        # Set up environment with correct Python path
        env = os.environ.copy()
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        env['PYTHONPATH'] = project_root
        
        result = subprocess.run(
            [sys.executable, script_path] + args,
            cwd=project_root,
            timeout=timeout_seconds,
            capture_output=False,  # Let output show in real-time
            text=True,
            env=env
        )
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully in {duration}")
            return True
        else:
            print(f"❌ {description} failed with exit code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out after {timeout_seconds} seconds")
        return False
    except Exception as e:
        print(f"❌ {description} failed with error: {e}")
        return False

def main():
    print("🏁 Starting Complete Player Data Ingestion")
    print(f"⏰ Total timeout: {TIMEOUT_HOURS} hours")
    print(f"📁 Player URL directory: {PLAYER_URL_DIR}")
    
    # Wait for files to be ready
    max_wait_time = 3600  # 1 hour max wait
    wait_start = time.time()
    
    while not check_files_exist():
        if time.time() - wait_start > max_wait_time:
            print("❌ Timed out waiting for URL files to be ready")
            return 1
        
        print("⏳ Waiting 60 seconds before checking again...")
        time.sleep(60)
    
    # Calculate timeouts for each script
    total_timeout_seconds = TIMEOUT_HOURS * 3600
    mlb_timeout = total_timeout_seconds // 3  # 1/3 of time for MLB
    milb_timeout = (total_timeout_seconds - mlb_timeout) // 5  # Remaining time split among 5 MiLB levels
    
    print(f"\n⏱️  Timeout allocation:")
    print(f"   MLB: {mlb_timeout // 3600:.1f} hours")
    print(f"   Each MiLB level: {milb_timeout // 3600:.1f} hours")
    
    # Track results
    results = []
    
    # 1. Run MLB ingestion
    mlb_script = os.path.join(os.path.dirname(__file__), 'ingest_bref_players.py')
    mlb_url_file = os.path.join(PLAYER_URL_DIR, 'mlb_player_urls.txt')
    
    if os.path.exists(mlb_script):
        success = run_script_with_timeout(
            mlb_script,
            [mlb_url_file],
            mlb_timeout,
            "MLB Player Ingestion"
        )
        results.append(("MLB", success))
    else:
        print(f"❌ MLB ingestion script not found: {mlb_script}")
        results.append(("MLB", False))
    
    # 2. Run MiLB ingestion for each level
    milb_script = os.path.join(os.path.dirname(__file__), 'ingest_milb_players.py')
    
    if not os.path.exists(milb_script):
        print(f"❌ MiLB ingestion script not found: {milb_script}")
        return 1
    
    milb_levels = [
        ('AAA', 'aaa_player_urls.txt'),
        ('AA', 'aa_player_urls.txt'),
        ('A+', 'a+_player_urls.txt'),
        ('A', 'a_player_urls.txt'),
        ('Rk', 'rk_player_urls.txt')
    ]
    
    for level, filename in milb_levels:
        url_file = os.path.join(PLAYER_URL_DIR, filename)
        
        if os.path.exists(url_file):
            success = run_script_with_timeout(
                milb_script,
                [url_file],
                milb_timeout,
                f"{level} Player Ingestion"
            )
            results.append((level, success))
        else:
            print(f"❌ URL file not found: {url_file}")
            results.append((level, False))
    
    # Summary
    print(f"\n📊 Ingestion Summary:")
    print("=" * 50)
    
    successful = 0
    failed = 0
    
    for level, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"   {level:4} | {status}")
        if success:
            successful += 1
        else:
            failed += 1
    
    print("=" * 50)
    print(f"   Total: {len(results)} levels")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    
    if failed == 0:
        print("🎉 All ingestion completed successfully!")
        return 0
    else:
        print("⚠️  Some ingestion failed. Check logs above.")
        return 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Ingestion interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 