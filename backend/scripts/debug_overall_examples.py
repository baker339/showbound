import sys
import os
import numpy as np

# Ensure backend directory is in sys.path for flat imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import SessionLocal
from ml_service import ml_service
import models

def print_stat_normalization():
    if hasattr(ml_service, 'data_driven_mins') and hasattr(ml_service, 'data_driven_maxs'):
        print("\n[DEBUG] Stat normalization anchors (min, max) for first 10 features:")
        for i, (mn, mx) in enumerate(zip(ml_service.data_driven_mins[:10], ml_service.data_driven_maxs[:10])):
            print(f"  Feature {i}: min={mn:.3f}, max={mx:.3f}")
    else:
        print("[DEBUG] No stat normalization anchors found.")

def get_player_overall(db, player):
    ptype = ml_service.get_player_type(player)
    player_id = getattr(player, 'id', None)
    if player_id is None:
        return None
    ratings = ml_service.calculate_mlb_show_ratings(db, int(player_id))
    if not ratings:
        return None
    if ptype == 'pitcher':
        return ratings.get('overall_rating')
    elif ptype in ('position_player', 'dh'):
        return ratings.get('overall_rating')
    elif ptype == 'two_way':
        hit = ratings.get('hitting', {}).get('overall_rating')
        pit = ratings.get('pitching', {}).get('overall_rating')
        if hit is not None and pit is not None:
            return (hit + pit) / 2
        elif hit is not None:
            return hit
        elif pit is not None:
            return pit
    return None

def print_examples(db, players, label):
    print(f"\n[DEBUG] {label}:")
    for player in players:
        overall = get_player_overall(db, player)
        if overall is not None:
            print(f"  {player.full_name:25s} ({ml_service.get_player_type(player):15s}): {overall:.2f}")
        else:
            print(f"  {player.full_name:25s} ({ml_service.get_player_type(player):15s}): No rating")

def print_sample_positions(db):
    print("\n[DEBUG] Sample MLB player positions (first 20):")
    players = db.query(models.Player).filter(models.Player.level == 'MLB').limit(20).all()
    for player in players:
        name = getattr(player, 'full_name', 'Unknown')
        pid = getattr(player, 'id', 'Unknown')
        primary_position = getattr(player, 'primary_position', None)
        positions = getattr(player, 'positions', None)
        print(f"  ID: {pid}, Name: {name}, primary_position: {primary_position}, positions: {positions}")

def main():
    db = SessionLocal()
    try:
        # 1. Recompute stat normalization
        print("[DEBUG] Recomputing stat normalization using all MLB players...")
        ml_service.compute_stat_normalization(db)
        print_stat_normalization()

        # Print sample positions for first 20 MLB players
        print_sample_positions(db)

        # 2. Find specific players
        names = ["Shohei Ohtani", "Aaron Judge", "Mike Trout", "Jacob deGrom"]
        for name in names:
            player = db.query(models.Player).filter(models.Player.full_name.ilike(f"%{name}%")).first()
            if player:
                print(f"\n[DEBUG] {name}:")
                overall = get_player_overall(db, player)
                print(f"  {player.full_name:25s} ({ml_service.get_player_type(player):15s}): {overall if overall is not None else 'No rating'}")
            else:
                print(f"\n[DEBUG] {name}: Not found in database.")

        # 3. Get all MLB players and their overalls
        players = db.query(models.Player).filter(models.Player.level == 'MLB').all()
        player_overalls = []
        for player in players:
            overall = get_player_overall(db, player)
            if overall is not None:
                player_overalls.append((player, overall, ml_service.get_player_type(player)))
        # Split by type
        pitchers = [p for p in player_overalls if p[2] == 'pitcher']
        batters = [p for p in player_overalls if p[2] in ('position_player', 'dh')]
        # Sort
        pitchers_sorted = sorted(pitchers, key=lambda x: x[1], reverse=True)
        batters_sorted = sorted(batters, key=lambda x: x[1], reverse=True)
        # Top 5, median 5, bottom 5
        def get_slices(arr):
            n = len(arr)
            if n == 0:
                return [], [], []
            top = arr[:5]
            mid = arr[n//2-2:n//2+3] if n >= 5 else arr
            bot = arr[-5:]
            return top, mid, bot
        for label, arr in [("Pitchers", pitchers_sorted), ("Batters", batters_sorted)]:
            top, mid, bot = get_slices(arr)
            print_examples(db, [x[0] for x in top], f"Top 5 {label}")
            print_examples(db, [x[0] for x in mid], f"Median 5 {label}")
            print_examples(db, [x[0] for x in bot], f"Bottom 5 {label}")
    finally:
        db.close()

if __name__ == "__main__":
    main() 