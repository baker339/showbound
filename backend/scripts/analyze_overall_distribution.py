import sys
import os
import numpy as np
from collections import Counter

# Ensure backend directory is in sys.path for flat imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import SessionLocal
from ml_service import ml_service
import models


def main():
    db = SessionLocal()
    try:
        players = db.query(models.Player).filter(models.Player.level == 'MLB').all()
        pitcher_overalls = []
        batter_overalls = []
        two_way_overalls = []
        missing = 0
        total = len(players)
        print(f"[DEBUG] Found {total} MLB players. Starting analysis...")
        for idx, player in enumerate(players):
            ptype = ml_service.get_player_type(player)
            name = getattr(player, 'full_name', f'ID {getattr(player, 'id', 'unknown')}')
            player_id = getattr(player, 'id', None)
            if player_id is None:
                print(f"[DEBUG]   Player {name} missing id, skipping.")
                missing += 1
                continue
            if idx % 100 == 0:
                print(f"[DEBUG] Processing player {idx+1}/{total}: {name} ({ptype})")
            player_id = int(player_id)
            ratings = ml_service.calculate_mlb_show_ratings(db, player_id)
            if not ratings:
                print(f"[DEBUG]   No ratings for {name} (ID {player_id}, type {ptype})")
                missing += 1
                continue
            if ptype == 'pitcher':
                pitcher_overalls.append(ratings.get('overall_rating'))
            elif ptype in ('position_player', 'dh'):
                batter_overalls.append(ratings.get('overall_rating'))
            elif ptype == 'two_way':
                # Take the mean of hitting and pitching overall
                hit = ratings.get('hitting', {}).get('overall_rating')
                pit = ratings.get('pitching', {}).get('overall_rating')
                if hit is not None and pit is not None:
                    two_way_overalls.append((hit + pit) / 2)
                elif hit is not None:
                    batter_overalls.append(hit)
                elif pit is not None:
                    pitcher_overalls.append(pit)
        print(f"[DEBUG] Finished processing all players.")
        def print_stats(name, arr):
            arr = [x for x in arr if x is not None]
            if not arr:
                print(f"No data for {name}.")
                return
            arr_np = np.array(arr)
            print(f"\n{name} Overall Ratings:")
            print(f"  Count: {len(arr_np)}")
            print(f"  Mean: {np.mean(arr_np):.2f}")
            print(f"  Median: {np.median(arr_np):.2f}")
            print(f"  Min: {np.min(arr_np):.2f}")
            print(f"  Max: {np.max(arr_np):.2f}")
            print(f"  Std: {np.std(arr_np):.2f}")
            # Simple histogram (bin size 5)
            bins = list(range(30, 111, 5))
            hist = Counter(((int(x) // 5) * 5 for x in arr_np))
            print("  Histogram (bin size 5):")
            for b in bins:
                print(f"    {b:3d}-{b+4:3d}: {hist.get(b, 0)}")
        print_stats("Pitchers", pitcher_overalls)
        print_stats("Batters", batter_overalls)
        print_stats("Two-way Players", two_way_overalls)
        print(f"\nPlayers with missing ratings: {missing}")
    finally:
        db.close()

if __name__ == "__main__":
    main() 