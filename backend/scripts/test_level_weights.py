#!/usr/bin/env python3

import os
import sys

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import SessionLocal
from ml_service import ml_service
import models

def test_level_weights():
    """Test the data-driven level weight computation"""
    print("Testing data-driven level weight computation...")
    
    db = SessionLocal()
    try:
        # Compute level weights from data
        ml_service.compute_level_weights_from_data(db)
        
        # Display the computed weights
        if hasattr(ml_service, 'data_driven_level_weights'):
            print("\nData-driven level weights:")
            for level, weight in ml_service.data_driven_level_weights.items():
                print(f"  {level}: {weight:.3f}")
        else:
            print("No data-driven weights computed")
        
        # Test the weighting on a few sample players
        print("\nTesting level weighting on sample players:")
        players = db.query(models.Player).limit(5).all()
        
        for player in players:
            player_level = getattr(player, 'level', None)
            level_factor = ml_service._get_level_factor(str(player_level) if player_level else 'Unknown')
            print(f"  {player.full_name} ({player_level}): weight = {level_factor:.3f}")
            
            # Get some sample stats
            bat_stats = db.query(models.StandardBattingStat).filter(
                models.StandardBattingStat.player_id == player.id
            ).first()
            
            if bat_stats:
                raw_hr = ml_service._safe_float(bat_stats.hr)
                weighted_hr = raw_hr * level_factor
                print(f"    Raw HR: {raw_hr}, Weighted HR: {weighted_hr:.1f}")
        
        # Test weighting comparison between levels
        print("\nTesting level weighting comparison:")
        mlb_player = db.query(models.Player).filter(models.Player.level == 'MLB').first()
        aaa_player = db.query(models.Player).filter(models.Player.level == 'AAA').first()
        
        if mlb_player and aaa_player:
            mlb_level_factor = ml_service._get_level_factor('MLB')
            aaa_level_factor = ml_service._get_level_factor('AAA')
            
            print(f"MLB player: {mlb_player.full_name}, weight = {mlb_level_factor:.3f}")
            print(f"AAA player: {aaa_player.full_name}, weight = {aaa_level_factor:.3f}")
            
            # Compare same raw stats
            raw_hr = 20.0
            mlb_weighted = raw_hr * mlb_level_factor
            aaa_weighted = raw_hr * aaa_level_factor
            
            print(f"Same raw HR ({raw_hr}):")
            print(f"  MLB weighted: {mlb_weighted:.1f}")
            print(f"  AAA weighted: {aaa_weighted:.1f}")
            print(f"  Difference: {mlb_weighted - aaa_weighted:.1f} HR")
        
    except Exception as e:
        print(f"Error testing level weights: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    test_level_weights() 