#!/usr/bin/env python3
"""
Player Development Pipeline Forecasting Service
Analyzes player development across MLB, MiLB, NCAA, and HS levels to forecast potential and timelines.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal
from backend import models
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, accuracy_score
import joblib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class DevelopmentPipelineService:
    def __init__(self):
        self.db = SessionLocal()
        self.scaler = StandardScaler()
        self.development_model = None
        self.timeline_model = None
        self.risk_model = None
        self.models_loaded = False
        
    def load_or_train_models(self):
        """Load pre-trained models or train new ones"""
        try:
            # Try to load existing models
            self.development_model = joblib.load('models/development_pipeline_model.pkl')
            self.timeline_model = joblib.load('models/timeline_model.pkl')
            self.risk_model = joblib.load('models/risk_model.pkl')
            self.scaler = joblib.load('models/scaler.pkl')
            self.models_loaded = True
            logger.info("✅ Loaded pre-trained development pipeline models")
        except FileNotFoundError:
            logger.info("🔄 Training new development pipeline models...")
            self._train_models()
    
    def _train_models(self):
        """Train models for development pipeline forecasting"""
        try:
            # Get training data from all levels
            training_data = self._prepare_training_data()
            
            if training_data.empty:
                logger.warning("⚠️  No training data available. Using sample models.")
                self._create_sample_models()
                return
            
            # Prepare features and targets
            X = training_data.drop(['mlb_debut_year', 'mlb_success', 'development_speed'], axis=1, errors='ignore')
            y_debut = training_data['mlb_debut_year']
            y_success = training_data['mlb_success']
            y_speed = training_data['development_speed']
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train development timeline model
            self.timeline_model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.timeline_model.fit(X_scaled, y_debut)
            
            # Train success prediction model
            self.development_model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.development_model.fit(X_scaled, y_success)
            
            # Train development speed model
            self.risk_model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.risk_model.fit(X_scaled, y_speed)
            
            # Save models
            os.makedirs('models', exist_ok=True)
            joblib.dump(self.development_model, 'models/development_pipeline_model.pkl')
            joblib.dump(self.timeline_model, 'models/timeline_model.pkl')
            joblib.dump(self.risk_model, 'models/risk_model.pkl')
            joblib.dump(self.scaler, 'models/scaler.pkl')
            
            self.models_loaded = True
            logger.info("✅ Development pipeline models trained and saved")
            
        except Exception as e:
            logger.error(f"❌ Error training models: {e}")
            self._create_sample_models()
    
    def _prepare_training_data(self) -> pd.DataFrame:
        """Prepare training data from all development levels"""
        try:
            # Get players with development timelines
            timelines = self.db.query(models.PlayerDevelopmentTimeline).all()
            
            if not timelines:
                return pd.DataFrame()
            
            training_data = []
            
            for timeline in timelines:
                # Get player/prospect info
                if timeline.player_id:
                    player = self.db.query(models.Player).filter(models.Player.id == timeline.player_id).first()
                elif timeline.prospect_id:
                    prospect = self.db.query(models.Prospect).filter(models.Prospect.id == timeline.prospect_id).first()
                    player = None
                else:
                    continue
                
                # Extract features from stats
                features = self._extract_features_from_timeline(timeline, player, prospect)
                
                if features:
                    training_data.append(features)
            
            return pd.DataFrame(training_data)
            
        except Exception as e:
            logger.error(f"❌ Error preparing training data: {e}")
            return pd.DataFrame()
    
    def _extract_features_from_timeline(self, timeline, player, prospect) -> Optional[Dict]:
        """Extract features from a development timeline entry"""
        try:
            stats = timeline.stats_json or {}
            
            features = {
                'level': self._encode_level(timeline.level),
                'season_year': timeline.season_year,
                'age': timeline.season_year - (prospect.graduation_year if prospect else 2000),
                
                # Hitting features
                'batting_avg': stats.get('batting_avg', 0.0),
                'on_base_pct': stats.get('on_base_pct', 0.0),
                'slugging_pct': stats.get('slugging_pct', 0.0),
                'ops': stats.get('ops', 0.0),
                'home_runs': stats.get('home_runs', 0),
                'rbi': stats.get('rbi', 0),
                'stolen_bases': stats.get('stolen_bases', 0),
                'walks': stats.get('walks', 0),
                'strikeouts': stats.get('strikeouts', 0),
                
                # Pitching features
                'era': stats.get('era', 10.0),  # High ERA for non-pitchers
                'wins': stats.get('wins', 0),
                'losses': stats.get('losses', 0),
                'innings_pitched': stats.get('innings_pitched', 0.0),
                'strikeouts_pitched': stats.get('strikeouts_pitched', 0),
                'walks_allowed': stats.get('walks_allowed', 0),
                'whip': stats.get('whip', 10.0),  # High WHIP for non-pitchers
                
                # Advanced features
                'exit_velocity': stats.get('avg_exit_velocity', 0.0),
                'barrel_pct': stats.get('barrel_pct', 0.0),
                'hard_hit_pct': stats.get('hard_hit_pct', 0.0),
                'sprint_speed': stats.get('sprint_speed', 0.0),
                'arm_strength': stats.get('arm_strength', 0.0),
            }
            
            # Add target variables (if available)
            if player:
                features['mlb_debut_year'] = timeline.season_year
                features['mlb_success'] = 1  # Made it to MLB
                features['development_speed'] = 'Fast' if timeline.season_year - (prospect.graduation_year if prospect else 2000) <= 3 else 'Normal'
            else:
                features['mlb_debut_year'] = None
                features['mlb_success'] = 0
                features['development_speed'] = 'Unknown'
            
            return features
            
        except Exception as e:
            logger.error(f"❌ Error extracting features: {e}")
            return None
    
    def _encode_level(self, level: str) -> int:
        """Encode development level as numeric"""
        level_map = {
            'HS': 1,
            'NCAA': 2,
            'MiLB': 3,
            'MLB': 4
        }
        return level_map.get(level, 0)
    
    def _create_sample_models(self):
        """Create sample models when no training data is available"""
        # Create dummy models for demonstration
        self.development_model = RandomForestClassifier(n_estimators=10, random_state=42)
        self.timeline_model = RandomForestRegressor(n_estimators=10, random_state=42)
        self.risk_model = RandomForestClassifier(n_estimators=10, random_state=42)
        
        # Train on dummy data
        X_dummy = np.random.rand(100, 20)
        y_dummy_debut = np.random.randint(2020, 2030, 100)
        y_dummy_success = np.random.randint(0, 2, 100)
        y_dummy_speed = np.random.choice(['Fast', 'Normal', 'Slow'], 100)
        
        self.scaler.fit(X_dummy)
        X_scaled = self.scaler.transform(X_dummy)
        
        self.timeline_model.fit(X_scaled, y_dummy_debut)
        self.development_model.fit(X_scaled, y_dummy_success)
        self.risk_model.fit(X_scaled, y_dummy_speed)
        
        self.models_loaded = True
        logger.info("✅ Created sample development pipeline models")
    
    def forecast_player_development(self, prospect_id: int) -> Dict:
        """Forecast a prospect's development timeline and potential"""
        try:
            if not self.models_loaded:
                self.load_or_train_models()
            
            prospect = self.db.query(models.Prospect).filter(models.Prospect.id == prospect_id).first()
            if not prospect:
                raise ValueError("Prospect not found")
            
            # Get prospect's current timeline
            timeline = self.db.query(models.PlayerDevelopmentTimeline).filter(
                models.PlayerDevelopmentTimeline.prospect_id == prospect_id
            ).first()
            
            if not timeline:
                # Create timeline entry if none exists
                timeline = self._create_timeline_entry(prospect)
            
            # Extract features for prediction
            features = self._extract_prospect_features(prospect, timeline)
            features_scaled = self.scaler.transform([features])
            
            # Make predictions
            projected_debut = int(self.timeline_model.predict(features_scaled)[0])
            success_probability = self.development_model.predict_proba(features_scaled)[0][1]
            development_speed = self.risk_model.predict(features_scaled)[0]
            
            # Calculate risk factors
            risk_factors = self._calculate_risk_factors(prospect, timeline)
            
            # Generate development projection
            projection = self._create_development_projection(
                prospect, projected_debut, success_probability, 
                development_speed, risk_factors
            )
            
            return projection
            
        except Exception as e:
            logger.error(f"❌ Error forecasting player development: {e}")
            return self._create_sample_projection(prospect_id)
    
    def _extract_prospect_features(self, prospect, timeline) -> List[float]:
        """Extract features from prospect for prediction"""
        stats = timeline.stats_json or {}
        
        features = [
            self._encode_level(prospect.level),
            timeline.season_year,
            timeline.season_year - (prospect.graduation_year or 2000),
            stats.get('batting_avg', 0.0),
            stats.get('on_base_pct', 0.0),
            stats.get('slugging_pct', 0.0),
            stats.get('ops', 0.0),
            stats.get('home_runs', 0),
            stats.get('rbi', 0),
            stats.get('stolen_bases', 0),
            stats.get('walks', 0),
            stats.get('strikeouts', 0),
            stats.get('era', 10.0),
            stats.get('wins', 0),
            stats.get('losses', 0),
            stats.get('innings_pitched', 0.0),
            stats.get('strikeouts_pitched', 0),
            stats.get('walks_allowed', 0),
            stats.get('whip', 10.0),
            stats.get('avg_exit_velocity', 0.0),
        ]
        
        return features
    
    def _calculate_risk_factors(self, prospect, timeline) -> Dict:
        """Calculate risk factors for prospect development"""
        stats = timeline.stats_json or {}
        
        # Injury risk based on position and usage
        injury_risk = 0.3  # Base risk
        if prospect.position == 'P':
            injury_risk += 0.2
        if stats.get('innings_pitched', 0) > 100:
            injury_risk += 0.1
        
        # Bust risk based on performance consistency
        bust_risk = 0.4  # Base risk
        if stats.get('batting_avg', 0) < 0.250:
            bust_risk += 0.2
        if stats.get('era', 10) > 5.0:
            bust_risk += 0.2
        
        # Breakout potential based on tools
        breakout_potential = 0.3  # Base potential
        if stats.get('avg_exit_velocity', 0) > 90:
            breakout_potential += 0.2
        if stats.get('sprint_speed', 0) > 28:
            breakout_potential += 0.1
        
        return {
            'injury_risk': min(injury_risk, 1.0),
            'bust_risk': min(bust_risk, 1.0),
            'breakout_potential': min(breakout_potential, 1.0)
        }
    
    def _create_development_projection(self, prospect, projected_debut, success_probability, 
                                     development_speed, risk_factors) -> Dict:
        """Create comprehensive development projection"""
        current_year = datetime.now().year
        
        # Calculate timeline projections
        years_to_debut = max(0, projected_debut - current_year)
        projected_peak = projected_debut + 3  # Peak typically 3 years after debut
        projected_career_length = 8 if success_probability > 0.7 else 4
        
        # Generate player comparisons
        ceiling_comparison = self._generate_player_comparison(prospect, 'ceiling')
        floor_comparison = self._generate_player_comparison(prospect, 'floor')
        
        # Create projection object
        projection = models.PlayerDevelopmentProjection(
            prospect_id=prospect.id,
            projection_year=current_year,
            confidence_level=success_probability,
            projected_mlb_debut=projected_debut,
            projected_mlb_peak=projected_peak,
            projected_career_length=projected_career_length,
            projected_stats_json=self._generate_projected_stats(prospect, projected_debut),
            projected_ratings_json=self._generate_projected_ratings(prospect, projected_debut),
            injury_risk=risk_factors['injury_risk'],
            bust_risk=risk_factors['bust_risk'],
            breakout_potential=risk_factors['breakout_potential'],
            development_speed=development_speed,
            ceiling_comparison=ceiling_comparison,
            floor_comparison=floor_comparison
        )
        
        # Save to database
        self.db.add(projection)
        self.db.commit()
        
        return {
            'prospect_id': prospect.id,
            'prospect_name': prospect.name,
            'projected_mlb_debut': projected_debut,
            'years_to_debut': years_to_debut,
            'success_probability': success_probability,
            'development_speed': development_speed,
            'projected_peak': projected_peak,
            'projected_career_length': projected_career_length,
            'risk_factors': risk_factors,
            'ceiling_comparison': ceiling_comparison,
            'floor_comparison': floor_comparison,
            'confidence_level': success_probability
        }
    
    def _create_timeline_entry(self, prospect) -> models.PlayerDevelopmentTimeline:
        """Create a timeline entry for a prospect"""
        timeline = models.PlayerDevelopmentTimeline(
            prospect_id=prospect.id,
            level=prospect.level,
            season_year=prospect.graduation_year or datetime.now().year,
            stats_json=prospect.stats_json,
            scouting_grades=self._generate_scouting_grades(prospect),
            development_notes=prospect.scouting_report,
            start_date=datetime.now(),
            created_at=datetime.now()
        )
        
        self.db.add(timeline)
        self.db.commit()
        return timeline
    
    def _generate_scouting_grades(self, prospect) -> Dict:
        """Generate 20-80 scouting grades for prospect"""
        stats = prospect.stats_json or {}
        
        # Simple grade generation based on stats
        grades = {
            'hit': 50,
            'power': 50,
            'run': 50,
            'arm': 50,
            'field': 50,
            'overall': 50
        }
        
        # Adjust based on position and stats
        if prospect.position == 'P':
            grades.update({
                'velocity': 50,
                'control': 50,
                'movement': 50,
                'overall': 50
            })
        
        return grades
    
    def _generate_player_comparison(self, prospect, comparison_type: str) -> str:
        """Generate MLB player comparison"""
        # This would use more sophisticated comparison logic
        # For now, return sample comparisons
        if comparison_type == 'ceiling':
            if prospect.position == 'P':
                return "Gerrit Cole"
            else:
                return "Mike Trout"
        else:  # floor
            if prospect.position == 'P':
                return "Average MLB reliever"
            else:
                return "Average MLB bench player"
    
    def _generate_projected_stats(self, prospect, debut_year: int) -> Dict:
        """Generate projected MLB stats"""
        # This would use more sophisticated projection models
        return {
            'batting_avg': 0.275,
            'home_runs': 15,
            'rbi': 65,
            'ops': 0.780,
            'war': 2.5
        }
    
    def _generate_projected_ratings(self, prospect, debut_year: int) -> Dict:
        """Generate projected MLB The Show style ratings"""
        return {
            'contact': 65,
            'power': 60,
            'speed': 70,
            'fielding': 65,
            'arm': 65,
            'overall': 65
        }
    
    def _create_sample_projection(self, prospect_id: int) -> Dict:
        """Create a sample projection when models aren't available"""
        return {
            'prospect_id': prospect_id,
            'prospect_name': 'Unknown',
            'projected_mlb_debut': 2026,
            'years_to_debut': 3,
            'success_probability': 0.6,
            'development_speed': 'Normal',
            'projected_peak': 2029,
            'projected_career_length': 6,
            'risk_factors': {
                'injury_risk': 0.3,
                'bust_risk': 0.4,
                'breakout_potential': 0.3
            },
            'ceiling_comparison': 'Average MLB starter',
            'floor_comparison': 'MLB bench player',
            'confidence_level': 0.6
        }
    
    def get_development_pipeline_summary(self) -> Dict:
        """Get summary of development pipeline data"""
        try:
            # Count prospects by level
            hs_prospects = self.db.query(models.Prospect).filter(models.Prospect.level == 'HS').count()
            ncaa_prospects = self.db.query(models.Prospect).filter(models.Prospect.level == 'NCAA').count()
            milb_prospects = self.db.query(models.Prospect).filter(models.Prospect.level == 'MiLB').count()
            mlb_players = self.db.query(models.Player).count()
            
            # Count teams by level
            hs_teams = self.db.query(models.HSTeam).count()
            ncaa_teams = self.db.query(models.NCAATeam).count()
            milb_teams = self.db.query(models.MiLBTeam).count()
            mlb_teams = self.db.query(models.Team).count()
            
            # Get recent projections
            recent_projections = self.db.query(models.PlayerDevelopmentProjection).order_by(
                models.PlayerDevelopmentProjection.projection_date.desc()
            ).limit(10).all()
            
            return {
                'prospects_by_level': {
                    'high_school': hs_prospects,
                    'ncaa': ncaa_prospects,
                    'milb': milb_prospects,
                    'mlb': mlb_players
                },
                'teams_by_level': {
                    'high_school': hs_teams,
                    'ncaa': ncaa_teams,
                    'milb': milb_teams,
                    'mlb': mlb_teams
                },
                'recent_projections': [
                    {
                        'prospect_name': p.prospect.name if p.prospect else 'Unknown',
                        'projected_debut': p.projected_mlb_debut,
                        'success_probability': p.confidence_level,
                        'development_speed': p.development_speed
                    }
                    for p in recent_projections
                ],
                'total_prospects': hs_prospects + ncaa_prospects + milb_prospects,
                'total_teams': hs_teams + ncaa_teams + milb_teams + mlb_teams
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting pipeline summary: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        self.db.close() 