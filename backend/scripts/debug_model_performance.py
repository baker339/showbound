#!/usr/bin/env python3

import os
import sys

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal
from backend.ml_service import ml_service
from backend import models
import numpy as np
import pandas as pd

def debug_model_performance():
    """Debug the model performance issues"""
    print("🔍 Debugging Model Performance Issues...")
    
    db = SessionLocal()
    try:
        # Get all MLB players
        players = db.query(models.Player).filter(models.Player.level == 'MLB').all()
        print(f"📊 Found {len(players)} MLB players")
        
        # Extract features and targets
        features_list = []
        targets_list = []
        player_names = []
        
        for player in players:
            player_id = getattr(player, 'id', None)
            if player_id is None:
                continue
                
            feats = ml_service.extract_player_features(db, int(player_id), mode='hitting')
            if feats is not None and np.any(feats["raw"] != 0):
                features_list.append(feats["normalized"])
                targets_list.append(np.mean(feats["normalized"]))
                player_names.append(player.full_name)
        
        print(f"✅ Extracted features for {len(features_list)} players")
        
        if len(features_list) < 10:
            print("❌ Not enough players with valid features for training")
            return
        
        # Convert to numpy arrays
        X = np.array(features_list)
        y = np.array(targets_list)
        
        print(f"📈 Feature matrix shape: {X.shape}")
        print(f"🎯 Target vector shape: {y.shape}")
        
        # Analyze the data
        print(f"\n📊 Data Analysis:")
        print(f"Target mean: {np.mean(y):.2f}")
        print(f"Target std: {np.std(y):.2f}")
        print(f"Target min: {np.min(y):.2f}")
        print(f"Target max: {np.max(y):.2f}")
        
        # Check for NaN or infinite values
        nan_count = np.isnan(X).sum()
        inf_count = np.isinf(X).sum()
        print(f"NaN values in features: {nan_count}")
        print(f"Inf values in features: {inf_count}")
        
        # Check feature ranges
        print(f"\n🔍 Feature Analysis:")
        for i in range(min(10, X.shape[1])):
            feature_mean = np.mean(X[:, i])
            feature_std = np.std(X[:, i])
            print(f"Feature {i}: mean={feature_mean:.2f}, std={feature_std:.2f}")
        
        # Show some example players and their targets
        print(f"\n👥 Sample Players and Targets:")
        for i in range(min(5, len(player_names))):
            print(f"{player_names[i]}: target={targets_list[i]:.2f}")
        
        # Check if targets are reasonable
        print(f"\n🎯 Target Quality Check:")
        reasonable_targets = [t for t in targets_list if 20 <= t <= 80]
        print(f"Targets in reasonable range (20-80): {len(reasonable_targets)}/{len(targets_list)}")
        
        if len(reasonable_targets) < len(targets_list) * 0.8:
            print("⚠️  Many targets are outside reasonable range!")
        
        # Show distribution of targets
        print(f"\n📊 Target Distribution:")
        bins = [0, 20, 40, 60, 80, 100]
        hist, _ = np.histogram(y, bins=bins)
        for i in range(len(bins)-1):
            print(f"Range {bins[i]}-{bins[i+1]}: {hist[i]} players")
        
        # Test a simple model
        print(f"\n🧪 Testing Simple Model:")
        from sklearn.linear_model import LinearRegression
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_squared_error, r2_score
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train simple linear regression
        simple_model = LinearRegression()
        simple_model.fit(X_train, y_train)
        y_pred_simple = simple_model.predict(X_test)
        
        rmse_simple = np.sqrt(mean_squared_error(y_test, y_pred_simple))
        r2_simple = r2_score(y_test, y_pred_simple)
        
        print(f"Simple Linear Regression:")
        print(f"  RMSE: {rmse_simple:.3f}")
        print(f"  R²: {r2_simple:.3f}")
        
        # Compare with just predicting the mean
        mean_pred = np.mean(y_train)
        y_pred_mean = np.full_like(y_test, mean_pred)
        rmse_mean = np.sqrt(mean_squared_error(y_test, y_pred_mean))
        r2_mean = r2_score(y_test, y_pred_mean)
        
        print(f"Predicting Mean:")
        print(f"  RMSE: {rmse_mean:.3f}")
        print(f"  R²: {r2_mean:.3f}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if r2_simple < 0.1:
            print("❌ Model performance is very poor. Issues:")
            print("   - Feature extraction may be problematic")
            print("   - Target calculation may be flawed")
            print("   - Data quality issues")
        elif r2_simple < 0.3:
            print("⚠️  Model performance is poor. Consider:")
            print("   - Better feature engineering")
            print("   - Different target calculation")
            print("   - More training data")
        else:
            print("✅ Model performance is reasonable")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    debug_model_performance() 