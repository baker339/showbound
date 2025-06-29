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

def debug_ml_service():
    """Debug the ML service training and prediction issues"""
    print("🔍 Debugging ML Service Issues...")
    
    db = SessionLocal()
    try:
        # Force retrain the models
        print("🔄 Retraining models...")
        ml_service.fit_models(db)
        
        print(f"📊 Model metrics after training:")
        print(f"  RMSE: {ml_service.metrics['rmse']}")
        print(f"  R²: {ml_service.metrics['r2']}")
        
        # Check if models are properly fitted
        print(f"\n🔍 Model Status:")
        print(f"  is_fitted: {ml_service.is_fitted}")
        print(f"  Has overall_rating_model: {hasattr(ml_service, 'overall_rating_model')}")
        print(f"  Has scaler_hit: {hasattr(ml_service, 'scaler_hit')}")
        print(f"  Has knn_model_hit: {hasattr(ml_service, 'knn_model_hit')}")
        
        if hasattr(ml_service, 'overall_rating_model'):
            print(f"  Model has estimators_: {hasattr(ml_service.overall_rating_model, 'estimators_')}")
        
        # Test prediction on a few players
        print(f"\n🧪 Testing Predictions:")
        players = db.query(models.Player).filter(models.Player.level == 'MLB').limit(5).all()
        
        for player in players:
            player_id = getattr(player, 'id', None)
            if player_id is None:
                continue
                
            print(f"\n👤 Player: {player.full_name}")
            
            # Get features
            feats = ml_service.extract_player_features(db, int(player_id), mode='hitting')
            if feats is None:
                print("  ❌ No features extracted")
                continue
                
            print(f"  Features shape: {feats['normalized'].shape}")
            print(f"  Raw features mean: {np.mean(feats['raw']):.2f}")
            print(f"  Normalized features mean: {np.mean(feats['normalized']):.2f}")
            
            # Test prediction
            try:
                if hasattr(ml_service, 'overall_rating_model') and hasattr(ml_service.overall_rating_model, 'estimators_'):
                    prediction = ml_service.overall_rating_model.predict([feats['normalized']])
                    print(f"  Model prediction: {prediction[0]:.2f}")
                else:
                    print("  ❌ Model not properly fitted")
            except Exception as e:
                print(f"  ❌ Prediction error: {e}")
            
            # Test ratings calculation
            try:
                ratings = ml_service.calculate_mlb_show_ratings(db, int(player_id))
                if ratings:
                    print(f"  Overall rating: {ratings.get('overall_rating', 'N/A')}")
                    print(f"  Confidence: {ratings.get('confidence_score', 'N/A')}")
                else:
                    print("  ❌ No ratings calculated")
            except Exception as e:
                print(f"  ❌ Ratings error: {e}")
        
        # Check the training data used
        print(f"\n📊 Training Data Analysis:")
        if hasattr(ml_service, 'Xh_scaled') and hasattr(ml_service, 'hitter_ids'):
            print(f"  Training data shape: {ml_service.Xh_scaled.shape}")
            print(f"  Number of hitter IDs: {len(ml_service.hitter_ids)}")
            
            # Check if training data matches test data
            if len(players) > 0:
                test_feats = ml_service.extract_player_features(db, int(players[0].id), mode='hitting')
                if test_feats is not None:
                    print(f"  Test features shape: {test_feats['normalized'].shape}")
                    print(f"  Training features shape: {ml_service.Xh_scaled.shape[1]}")
                    
                    if test_feats['normalized'].shape[0] != ml_service.Xh_scaled.shape[1]:
                        print("  ⚠️  Feature dimension mismatch!")
                        print("  This could be causing the poor performance.")
        
        # Test the metrics endpoint
        print(f"\n📈 Testing Metrics Endpoint:")
        try:
            # Simulate what the metrics endpoint does
            if hasattr(ml_service, 'overall_rating_model') and hasattr(ml_service.overall_rating_model, 'estimators_'):
                print("  ✅ Model is properly fitted")
                print(f"  Current metrics: {ml_service.metrics}")
            else:
                print("  ❌ Model is not properly fitted")
                print("  This explains the poor metrics!")
        except Exception as e:
            print(f"  ❌ Error checking metrics: {e}")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    debug_ml_service() 