import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging
import datetime
from sklearn.decomposition import PCA
import models
from models import Player, PlayerFeatures, StandardBattingStat, ValueBattingStat, AdvancedBattingStat, StandardPitchingStat, ValuePitchingStat, AdvancedPitchingStat, StandardFieldingStat, LevelWeights
import re
import time

logger = logging.getLogger(__name__)

class BaseballMLService:
    def __init__(self):
        self.scaler = StandardScaler()
        self.knn_model = NearestNeighbors(n_neighbors=10, algorithm='ball_tree')
        self.overall_rating_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.pca = PCA(n_components=1)
        self.pca_weights = None
        self.is_fitted = False
        self.last_n_players = 0
        self.last_n_stats = 0
        self.metrics: dict[str, Optional[float]] = {"rmse": None, "r2": None}
        self._feature_cache = {}
        self._cache_last_loaded = None
        
    def refresh_feature_cache(self, db: Session):
        """Load all player features from the player_features table into memory."""
        self._feature_cache = {}
        for pf in db.query(PlayerFeatures).all():
            self._feature_cache[pf.player_id] = {
                "raw": pf.raw_features,
                "normalized": pf.normalized_features,
                "last_updated": pf.last_updated
            }
        self._cache_last_loaded = datetime.datetime.utcnow()
        print(f"[CACHE] Loaded {len(self._feature_cache)} player features into memory.")

    def get_cached_features(self, db: Session, player_id: int):
        # First check in-memory cache
        cached = self._feature_cache.get(player_id)
        if cached is not None:
            return cached
        # If not in cache, check the PlayerFeatures table in the DB
        pf = db.query(PlayerFeatures).filter(PlayerFeatures.player_id == player_id).first()
        if pf is not None:
            # Add to in-memory cache for future use
            self._feature_cache[player_id] = {
                "raw": pf.raw_features,
                "normalized": pf.normalized_features,
                "last_updated": pf.last_updated
            }
            return self._feature_cache[player_id]
        return None
        
    def compute_stat_normalization(self, db: Session):
        """Compute min/max (or percentiles) for each stat from MLB data and cache them."""
        players = db.query(Player).all()
        first_feats = None
        for player in players:
            player_id = getattr(player, 'id', None)
            if player_id is None:
                continue
            first_feats = self.extract_player_features(db, int(player_id))
            if first_feats is not None:
                break
        if first_feats is None:
            print("[ML] No player features found for normalization.")
            return
        feature_len = len(first_feats['raw'])
        stat_lists = [[] for _ in range(feature_len)]
        for player in players:
            player_id = getattr(player, 'id', None)
            if player_id is None:
                continue
            feats = self.extract_player_features(db, int(player_id))
            if feats is None:
                continue
            for i, val in enumerate(feats['raw']):
                if val is not None and val != 0:
                    stat_lists[i].append(val)
        # Use 10th and 90th percentiles for more spread, only on non-zero, non-missing values
        mins = np.array([np.percentile(stat, 10) if stat else 0.0 for stat in stat_lists])
        maxs = np.array([np.percentile(stat, 90) if stat else 1.0 for stat in stat_lists])
        self.data_driven_mins = mins
        self.data_driven_maxs = maxs
        print("[ML] Data-driven normalization mins:", mins)
        print("[ML] Data-driven normalization maxs:", maxs)

    def _normalize_features(self, features: np.ndarray) -> np.ndarray:
        if hasattr(self, 'data_driven_mins') and hasattr(self, 'data_driven_maxs'):
            mins = self.data_driven_mins
            maxs = self.data_driven_maxs
        else:
            # Updated min/max arrays for expanded feature vector. These are rough MLB ranges; data-driven normalization is preferred.
            mins = np.array([
                0.200, 0.250, 80, 20, 10,  # Batting: BA, OBP, EV, HardHit%, LD%
                0.300, 0.1, 0, 0,          # SLG, ISO, Barrel%, HR
                5, 10, 10, 50,             # BB%, SO%, BB, SO
                0, -10,                    # SB, rbaser
                0.95, -20, -20,            # fld_pct, rdrs, rtot
                0, 0,                      # a, dp
                # Pitching (expanded)
                10, 2, 0,                  # k_pct, bb_pct, hr_pct
                1.5, 1.5, 0.8, 50,         # era, fip, whip, era_plus
                0, -5, -20,                # war, waa, raa
                0, 0, 0, 0,                # so, bb, ip, gs
                3, 1, 0.5, 5,              # so9, bb9, hr9, h9
                0.200, 60, 40, 40, 40, 2.0,# babip, lob_pct, era_minus, fip_minus, xfip_minus, siera
                -5, -20, -5,               # wpa, re24, cwpa
                0, 0                       # level_factor, age_factor
            ])
            maxs = np.array([
                0.350, 0.450, 100, 55, 35, # Batting: BA, OBP, EV, HardHit%, LD%
                0.700, 0.35, 20, 60,       # SLG, ISO, Barrel%, HR
                18, 35, 150, 250,          # BB%, SO%, BB, SO
                60, 10,                    # SB, rbaser
                1.0, 20, 20,               # fld_pct, rdrs, rtot
                50, 50,                    # a, dp
                # Pitching (expanded)
                50, 15, 10,                # k_pct, bb_pct, hr_pct
                7.0, 5.0, 2.5, 250,        # era, fip, whip, era_plus
                12, 10, 20,                # war, waa, raa
                350, 100, 250, 40,         # so, bb, ip, gs
                15, 7, 3, 12,              # so9, bb9, hr9, h9
                0.350, 90, 80, 80, 80, 6.0,# babip, lob_pct, era_minus, fip_minus, xfip_minus, siera
                10, 40, 10,                # wpa, re24, cwpa
                100, 100                   # level_factor, age_factor
            ])
        # Avoid divide by zero: if max==min, set normed to 0
        normed = np.zeros_like(features, dtype=float)
        for i in range(len(features)):
            if maxs[i] == mins[i]:
                normed[i] = 0.0
            else:
                normed[i] = (features[i] - mins[i]) / (maxs[i] - mins[i]) * 100
        normed = np.clip(normed, 0, 100)
        # Replace any nan with 0
        normed = np.nan_to_num(normed, nan=0.0)
        return normed
    
    def _pca_composite_score(self, features: np.ndarray) -> float:
        if self.pca_weights is not None:
            return float(np.dot(features, self.pca_weights))
        return float(np.mean(features))
    
    def _infer_level(self, db, player_id):
        # Try to infer from most recent stat table
        bat = db.query(StandardBattingStat).filter(StandardBattingStat.player_id == player_id).order_by(StandardBattingStat.season.desc()).first()
        pit = db.query(StandardPitchingStat).filter(StandardPitchingStat.player_id == player_id).order_by(StandardPitchingStat.season.desc()).first()
        stat = bat if (bat and (not pit or (bat.season or 0) >= (pit.season or 0))) else pit
        if stat and hasattr(stat, 'team') and stat.team:
            team = stat.team.lower()
            if team in ["yankees", "dodgers", "red sox", "cubs", "braves", "astros", "mets", "giants", "padres", "cardinals"]:
                return "MLB"
            elif team in ["rainiers", "stripers", "ironpigs", "sounds", "bisons", "chihuahuas", "express", "river cats", "isotopes", "bulls"]:
                return "AAA"
        return "AA"  # Default fallback
    
    def _get_level_factor(self, level: str) -> float:
        """Convert level to factor for MLB readiness and stat weighting"""
        # Default weights if no data-driven analysis has been done
        default_level_factors = {
            'MLB': 1.0,      # Full weight for MLB stats
            'AAA': 0.8,      # 80% weight for AAA stats
            'AA': 0.6,       # 60% weight for AA stats
            'A+': 0.4,       # 40% weight for A+ stats
            'A': 0.3,        # 30% weight for A stats
            'Rk': 0.2,       # 20% weight for Rookie stats
            'HS': 0.1,       # 10% weight for HS stats
            'NCAA': 0.2,     # 20% weight for NCAA stats
        }
        
        # Use data-driven weights if available, otherwise fall back to defaults
        if hasattr(self, 'data_driven_level_weights'):
            return self.data_driven_level_weights.get(level, default_level_factors.get(level, 0.5))
        else:
            return default_level_factors.get(level, 0.5)
    
    def compute_level_weights_from_data(self, db: Session, force: bool = False):
        """Compute data-driven level weights by analyzing performance differences between levels"""
        # Only recompute if not already computed, unless force=True
        if not force and hasattr(self, 'data_driven_level_weights') and isinstance(getattr(self, 'data_driven_level_weights', None), dict) and getattr(self, 'data_driven_level_weights', None):
            return
        if force or not hasattr(self, 'data_driven_level_weights') or not isinstance(getattr(self, 'data_driven_level_weights', None), dict) or not getattr(self, 'data_driven_level_weights', None):
            print("[ML] Computing data-driven level weights...")
            
            # Get all players with stats
            players = db.query(Player).all()
            
            # Collect stats by level
            level_stats = {
                'MLB': {'batting': [], 'pitching': []},
                'AAA': {'batting': [], 'pitching': []},
                'AA': {'batting': [], 'pitching': []},
                'A+': {'batting': [], 'pitching': []},
                'A': {'batting': [], 'pitching': []},
                'Rk': {'batting': [], 'pitching': []}
            }
            
            # Collect batting stats by level
            for player in players:
                player_level = getattr(player, 'level', None)
                if not player_level or player_level not in level_stats:
                    continue
                    
                # Get latest batting stats
                bat_stats = db.query(StandardBattingStat).filter(
                    StandardBattingStat.player_id == player.id
                ).order_by(StandardBattingStat.season.desc()).first()
                
                if bat_stats:
                    # Collect key batting metrics
                    stats_dict = {
                        'ba': self._safe_float(bat_stats.ba),
                        'obp': self._safe_float(bat_stats.obp),
                        'slg': self._safe_float(bat_stats.slg),
                        'hr': self._safe_float(bat_stats.hr),
                        'bb': self._safe_float(bat_stats.bb),
                        'so': self._safe_float(bat_stats.so),
                        'sb': self._safe_float(bat_stats.sb),
                        'pa': self._safe_float(bat_stats.pa)
                    }
                    # Only include if player had meaningful playing time
                    if stats_dict['pa'] > 50:
                        level_stats[player_level]['batting'].append(stats_dict)
                
                # Get latest pitching stats
                pit_stats = db.query(StandardPitchingStat).filter(
                    StandardPitchingStat.player_id == player.id
                ).order_by(StandardPitchingStat.season.desc()).first()
                
                if pit_stats:
                    # Collect key pitching metrics
                    stats_dict = {
                        'era': self._safe_float(pit_stats.era),
                        'ip': self._safe_float(pit_stats.ip),
                        'so': self._safe_float(pit_stats.so),
                        'bb': self._safe_float(pit_stats.bb),
                        'era_plus': self._safe_float(pit_stats.era_plus),
                        'whip': self._safe_float(pit_stats.whip)
                    }
                    # Only include if player had meaningful innings
                    if stats_dict['ip'] and float(stats_dict['ip']) > 10:
                        level_stats[player_level]['pitching'].append(stats_dict)
            
            # Calculate level weights based on performance differences
            level_weights = {}
            
            # Use MLB as baseline (1.0)
            level_weights['MLB'] = 1.0
            
            # Calculate batting weights
            mlb_batting_avg = self._calculate_avg_performance(level_stats['MLB']['batting'])
            if mlb_batting_avg:
                for level in ['AAA', 'AA', 'A+', 'A', 'Rk']:
                    if level_stats[level]['batting']:
                        level_avg = self._calculate_avg_performance(level_stats[level]['batting'])
                        if level_avg and mlb_batting_avg:
                            # Calculate weight based on performance ratio
                            batting_weight = self._calculate_performance_ratio(level_avg, mlb_batting_avg)
                            level_weights[level] = batting_weight
            
            # Calculate pitching weights (inverse for ERA - lower is better)
            mlb_pitching_avg = self._calculate_avg_performance(level_stats['MLB']['pitching'])
            if mlb_pitching_avg:
                for level in ['AAA', 'AA', 'A+', 'A', 'Rk']:
                    if level_stats[level]['pitching']:
                        level_avg = self._calculate_avg_performance(level_stats[level]['pitching'])
                        if level_avg and mlb_pitching_avg:
                            # For pitching, lower ERA is better, so we invert the ratio
                            pitching_weight = self._calculate_performance_ratio(mlb_pitching_avg, level_avg)
                            # Combine with existing batting weight if available
                            if level in level_weights:
                                level_weights[level] = (level_weights[level] + pitching_weight) / 2
                            else:
                                level_weights[level] = pitching_weight
            
            # Ensure weights are reasonable (between 0.1 and 1.0)
            for level in level_weights:
                level_weights[level] = max(0.1, min(1.0, level_weights[level]))
            
            # Store the computed weights
            self.data_driven_level_weights = level_weights
            
            print(f"[ML] Data-driven level weights computed: {level_weights}")
    
    def _safe_float(self, val):
        """Safely convert value to float"""
        try:
            return float(val) if val is not None else 0.0
        except (TypeError, ValueError):
            return 0.0
    
    def _calculate_avg_performance(self, stats_list):
        """Calculate average performance across multiple stats"""
        if not stats_list:
            return None
        
        # Define which stats to use for performance calculation
        batting_metrics = ['ba', 'obp', 'slg', 'hr', 'bb', 'so', 'sb']
        pitching_metrics = ['era', 'so', 'bb', 'era_plus', 'whip']
        
        # Determine if this is batting or pitching stats
        if 'ba' in stats_list[0]:
            metrics = batting_metrics
        else:
            metrics = pitching_metrics
        
        # Calculate averages for each metric
        averages = {}
        for metric in metrics:
            values = [self._safe_float(stat.get(metric, 0)) for stat in stats_list]
            values = [v for v in values if v > 0]  # Filter out zeros
            if values:
                averages[metric] = np.mean(values)
        
        return averages if averages else None
    
    def _calculate_performance_ratio(self, level_avg, mlb_avg):
        """Calculate performance ratio between levels"""
        if not level_avg or not mlb_avg:
            return 0.5  # Default fallback
        
        # Calculate weighted average of performance ratios
        ratios = []
        weights = []
        
        # Batting metrics (higher is better)
        batting_metrics = ['ba', 'obp', 'slg', 'hr', 'bb', 'sb']
        for metric in batting_metrics:
            if metric in level_avg and metric in mlb_avg and mlb_avg[metric] > 0:
                ratio = level_avg[metric] / mlb_avg[metric]
                ratios.append(ratio)
                weights.append(1.0)  # Equal weight for now
        
        # Pitching metrics (lower ERA is better, higher SO is better)
        if 'era' in level_avg and 'era' in mlb_avg and mlb_avg['era'] > 0:
            # Invert ERA ratio since lower is better
            era_ratio = mlb_avg['era'] / level_avg['era']
            ratios.append(era_ratio)
            weights.append(1.0)
        
        if 'so' in level_avg and 'so' in mlb_avg and mlb_avg['so'] > 0:
            so_ratio = level_avg['so'] / mlb_avg['so']
            ratios.append(so_ratio)
            weights.append(1.0)
        
        # Calculate weighted average
        if ratios:
            weighted_avg = float(np.average(ratios, weights=weights))
            return max(0.1, min(1.0, weighted_avg))  # Clamp between 0.1 and 1.0
        
        return 0.5  # Default fallback
    
    def extract_player_features(self, db: Session, player_id: int, mode: str = 'all', season: Optional[int] = None) -> Optional[dict]:
        start = time.time()
        """Extract feature vector for a player, split by mode: 'hitting', 'pitching', or 'all' (default). If season is provided, fetch stats for that season."""
        try:
            player = db.query(Player).filter(Player.id == player_id).first()
            if not player:
                return None
            player_level = getattr(player, 'level', 'MLB')
            level_factor = self._get_level_factor(player_level)
            # Helper to aggregate all available values for a feature from a given model and column
            def aggregate_feature(model, attr, is_percentage=False):
                q = db.query(model).filter(model.player_id == player_id)
                if season is not None and hasattr(model, 'season'):
                    q = q.filter(model.season == str(season))
                vals = [getattr(row, attr, None) for row in q.all() if getattr(row, attr, None) not in (None, "")]
            def safe_float(val):
                try:
                    return float(val)
                except (TypeError, ValueError):
                        return None
                vals = [safe_float(v) for v in vals if safe_float(v) is not None]
                if not vals:
                    return None
                mean_val = float(np.mean([v for v in vals if v is not None]))
                if is_percentage:
                    if mean_val > 0.5:
                        diff_from_avg = mean_val - 0.250
                        weighted_diff = diff_from_avg * level_factor
                        return 0.250 + weighted_diff
                    else:
                        return mean_val * level_factor
                else:
                    return mean_val * level_factor
            # Build feature lists from correct tables
            hitting_feats = [
                aggregate_feature(StandardBattingStat, 'ba', is_percentage=True),
                aggregate_feature(StandardBattingStat, 'obp', is_percentage=True),
                aggregate_feature(AdvancedBattingStat, 'ev'),
                aggregate_feature(AdvancedBattingStat, 'hardh_pct', is_percentage=True),
                aggregate_feature(AdvancedBattingStat, 'ld_pct', is_percentage=True),
                aggregate_feature(StandardBattingStat, 'slg', is_percentage=True),
                aggregate_feature(AdvancedBattingStat, 'iso', is_percentage=True),
                aggregate_feature(AdvancedBattingStat, 'barrel_pct', is_percentage=True),
                aggregate_feature(StandardBattingStat, 'hr'),
                aggregate_feature(AdvancedBattingStat, 'bb_pct', is_percentage=True),
                aggregate_feature(AdvancedBattingStat, 'so_pct', is_percentage=True),
                aggregate_feature(StandardBattingStat, 'bb'),
                aggregate_feature(StandardBattingStat, 'so'),
                aggregate_feature(StandardBattingStat, 'sb'),
                aggregate_feature(ValueBattingStat, 'rbaser'),
            ]
            fielding_feats = [
                aggregate_feature(StandardFieldingStat, 'fld_pct', is_percentage=True),
                aggregate_feature(StandardFieldingStat, 'rdrs'),
                aggregate_feature(StandardFieldingStat, 'rtot'),
                aggregate_feature(StandardFieldingStat, 'a'),
                aggregate_feature(StandardFieldingStat, 'dp'),
            ]
            pitching_feats = [
                aggregate_feature(AdvancedPitchingStat, 'k_pct', is_percentage=True),
                aggregate_feature(AdvancedPitchingStat, 'bb_pct', is_percentage=True),
                aggregate_feature(AdvancedPitchingStat, 'hr_pct', is_percentage=True),
                aggregate_feature(StandardPitchingStat, 'era'),
                aggregate_feature(StandardPitchingStat, 'fip'),
                aggregate_feature(StandardPitchingStat, 'whip'),
                aggregate_feature(StandardPitchingStat, 'era_plus'),
                aggregate_feature(ValuePitchingStat, 'war'),
                aggregate_feature(ValuePitchingStat, 'waa'),
                aggregate_feature(ValuePitchingStat, 'raa'),
                aggregate_feature(StandardPitchingStat, 'so'),
                aggregate_feature(StandardPitchingStat, 'bb'),
                aggregate_feature(StandardPitchingStat, 'ip'),
                aggregate_feature(StandardPitchingStat, 'gs'),
                aggregate_feature(StandardPitchingStat, 'so9'),
                aggregate_feature(StandardPitchingStat, 'bb9'),
                aggregate_feature(StandardPitchingStat, 'hr9'),
                aggregate_feature(StandardPitchingStat, 'h9'),
                aggregate_feature(AdvancedPitchingStat, 'babip', is_percentage=True),
                aggregate_feature(AdvancedPitchingStat, 'lob_pct', is_percentage=True),
                aggregate_feature(AdvancedPitchingStat, 'era_minus'),
                aggregate_feature(AdvancedPitchingStat, 'fip_minus'),
                aggregate_feature(AdvancedPitchingStat, 'xfip_minus'),
                aggregate_feature(AdvancedPitchingStat, 'siera'),
                aggregate_feature(AdvancedPitchingStat, 'wpa'),
                aggregate_feature(AdvancedPitchingStat, 're24'),
                aggregate_feature(AdvancedPitchingStat, 'cwpa'),
            ]
            # Combine features based on mode
            if mode == 'hitting':
                feats = hitting_feats + fielding_feats + [level_factor * 100, 1.0]
            elif mode == 'pitching':
                feats = pitching_feats + fielding_feats + [level_factor * 100, 1.0]
            else:
                feats = hitting_feats + fielding_feats + pitching_feats + [level_factor * 100, 1.0]
            # Only keep present features for normalization and rating
            present_feats = [f for f in feats if f is not None]
            normed = self._normalize_features(np.array([f if f is not None else 0.0 for f in feats]))
            # Confidence: percent of features present
            confidence = 100.0 * len(present_feats) / len(feats) if feats else 0.0
            return {"raw": np.array([f if f is not None else 0.0 for f in feats]), "normalized": normed, "level": player_level, "level_factor": level_factor, "confidence": confidence, "present": [f is not None for f in feats]}
        except Exception as e:
            logger.error(f"Error extracting features for player {player_id}: {e}")
            return None
    
    def _get_age_factor(self, graduation_year: int) -> float:
        """Convert graduation year to age factor"""
        if not graduation_year:
            return 0.5
        current_year = 2025
        age = current_year - graduation_year + 18  # Assuming HS graduation at 18
        # Age factor: peak around 25-27, decline after 30
        if age < 20:
            return 0.7
        elif age < 25:
            return 0.9
        elif age < 30:
            return 1.0
        else:
            return max(0.6, 1.0 - (age - 30) * 0.05)
    
    def fit_models(self, db: Session):
        """Fit separate models for pitchers and position players using the correct feature sets."""
        try:
            # Compute data-driven level weights first (do not force recompute unless needed)
            self.compute_level_weights_from_data(db, force=False)
            
            # Only use MLB players for training the comparison models
            players = db.query(Player).filter(Player.level == 'MLB').all()
            pitcher_feats, pitcher_ids, pitcher_overalls = [], [], []
            hitter_feats, hitter_ids, hitter_overalls = [], [], []
            
            for player in players:
                player_id = getattr(player, 'id', None)
                if player_id is None:
                    continue
                ptype = self.get_player_type(player)
                if ptype == 'pitcher':
                    feats = self.extract_player_features(db, int(player_id), mode='pitching')
                    if feats is not None and np.any(feats["raw"] != 0):
                        pitcher_feats.append(feats["normalized"])
                        pitcher_ids.append(int(player_id))
                        # Use a more meaningful target for pitchers: weighted combination of key pitching metrics
                        raw_feats = feats["raw"]
                        # Key pitching metrics: ERA (inverted), K%, BB% (inverted), WHIP (inverted), WAR
                        era_score = max(0, 100 - raw_feats[3] * 10) if raw_feats[3] > 0 else 50  # ERA: lower is better
                        k_score = raw_feats[0] if raw_feats[0] > 0 else 50  # K%
                        bb_score = max(0, 100 - raw_feats[1] * 2) if raw_feats[1] > 0 else 50  # BB%: lower is better
                        whip_score = max(0, 100 - raw_feats[5] * 20) if raw_feats[5] > 0 else 50  # WHIP: lower is better
                        war_score = min(100, raw_feats[7] * 10) if raw_feats[7] > 0 else 50  # WAR
                        
                        # Weighted average of key metrics
                        pitcher_target = (era_score * 0.25 + k_score * 0.25 + bb_score * 0.2 + whip_score * 0.2 + war_score * 0.1)
                        pitcher_overalls.append(pitcher_target)
                elif ptype in ('position_player', 'dh'):
                    feats = self.extract_player_features(db, int(player_id), mode='hitting')
                    if feats is not None and np.any(feats["raw"] != 0):
                        hitter_feats.append(feats["normalized"])
                        hitter_ids.append(int(player_id))
                        # Use a more meaningful target for hitters: weighted combination of key hitting metrics
                        raw_feats = feats["raw"]
                        # Key hitting metrics: BA, OBP, SLG, HR, BB%, SO% (inverted), SB, WAR
                        ba_score = raw_feats[0] * 100 if raw_feats[0] > 0 else 50  # BA
                        obp_score = raw_feats[1] * 100 if raw_feats[1] > 0 else 50  # OBP
                        slg_score = raw_feats[5] * 100 if raw_feats[5] > 0 else 50  # SLG
                        hr_score = min(100, raw_feats[8] * 2) if raw_feats[8] > 0 else 50  # HR
                        bb_score = raw_feats[9] if raw_feats[9] > 0 else 50  # BB%
                        so_score = max(0, 100 - raw_feats[10]) if raw_feats[10] > 0 else 50  # SO%: lower is better
                        sb_score = min(100, raw_feats[13] * 2) if raw_feats[13] > 0 else 50  # SB
                        war_score = min(100, raw_feats[14] * 10) if raw_feats[14] > 0 else 50  # WAR (rbaser as proxy)
                        
                        # Weighted average of key metrics
                        hitter_target = (ba_score * 0.2 + obp_score * 0.2 + slg_score * 0.15 + hr_score * 0.1 + 
                                       bb_score * 0.1 + so_score * 0.1 + sb_score * 0.05 + war_score * 0.1)
                        hitter_overalls.append(hitter_target)
                elif ptype == 'two_way':
                    # Add to both
                    feats_hit = self.extract_player_features(db, int(player_id), mode='hitting')
                    feats_pit = self.extract_player_features(db, int(player_id), mode='pitching')
                    if feats_hit is not None and np.any(feats_hit["raw"] != 0):
                        hitter_feats.append(feats_hit["normalized"])
                        hitter_ids.append(int(player_id))
                        # Calculate hitting target for two-way player
                        raw_feats = feats_hit["raw"]
                        ba_score = raw_feats[0] * 100 if raw_feats[0] > 0 else 50
                        obp_score = raw_feats[1] * 100 if raw_feats[1] > 0 else 50
                        slg_score = raw_feats[5] * 100 if raw_feats[5] > 0 else 50
                        hr_score = min(100, raw_feats[8] * 2) if raw_feats[8] > 0 else 50
                        bb_score = raw_feats[9] if raw_feats[9] > 0 else 50
                        so_score = max(0, 100 - raw_feats[10]) if raw_feats[10] > 0 else 50
                        sb_score = min(100, raw_feats[13] * 2) if raw_feats[13] > 0 else 50
                        war_score = min(100, raw_feats[14] * 10) if raw_feats[14] > 0 else 50
                        hitter_target = (ba_score * 0.2 + obp_score * 0.2 + slg_score * 0.15 + hr_score * 0.1 + 
                                       bb_score * 0.1 + so_score * 0.1 + sb_score * 0.05 + war_score * 0.1)
                        hitter_overalls.append(hitter_target)
                    if feats_pit is not None and np.any(feats_pit["raw"] != 0):
                        pitcher_feats.append(feats_pit["normalized"])
                        pitcher_ids.append(int(player_id))
                        # Calculate pitching target for two-way player
                        raw_feats = feats_pit["raw"]
                        era_score = max(0, 100 - raw_feats[3] * 10) if raw_feats[3] > 0 else 50
                        k_score = raw_feats[0] if raw_feats[0] > 0 else 50
                        bb_score = max(0, 100 - raw_feats[1] * 2) if raw_feats[1] > 0 else 50
                        whip_score = max(0, 100 - raw_feats[5] * 20) if raw_feats[5] > 0 else 50
                        war_score = min(100, raw_feats[7] * 10) if raw_feats[7] > 0 else 50
                        pitcher_target = (era_score * 0.25 + k_score * 0.25 + bb_score * 0.2 + whip_score * 0.2 + war_score * 0.1)
                        pitcher_overalls.append(pitcher_target)
            
            # Fit pitcher model
            if len(pitcher_feats) >= 10:
                Xp = np.array(pitcher_feats)
                yp = np.array(pitcher_overalls)
                self.scaler_pit = StandardScaler().fit(Xp)
                self.knn_model_pit = NearestNeighbors(n_neighbors=10, algorithm='ball_tree').fit(self.scaler_pit.transform(Xp))
                self.pca_pit = PCA(n_components=1).fit(Xp)
                self.pca_weights_pit = self.pca_pit.components_[0]
                self.pitcher_ids = pitcher_ids
                self.Xp_scaled = self.scaler_pit.transform(Xp)
            
            # Fit hitter model
            if len(hitter_feats) >= 10:
                Xh = np.array(hitter_feats)
                yh = np.array(hitter_overalls)
                self.scaler_hit = StandardScaler().fit(Xh)
                self.knn_model_hit = NearestNeighbors(n_neighbors=10, algorithm='ball_tree').fit(self.scaler_hit.transform(Xh))
                self.pca_hit = PCA(n_components=1).fit(Xh)
                self.pca_weights_hit = self.pca_hit.components_[0]
                self.hitter_ids = hitter_ids
                self.Xh_scaled = self.scaler_hit.transform(Xh)
                
                # --- Train RandomForestRegressor for overall rating and compute metrics ---
                if len(Xh) > 10:
                    X_train, X_test, y_train, y_test = train_test_split(Xh, yh, test_size=0.2, random_state=42)
                    self.overall_rating_model.fit(X_train, y_train)
                    y_pred = self.overall_rating_model.predict(X_test)
                    self.metrics['rmse'] = float(mean_squared_error(y_test, y_pred) ** 0.5)
                    self.metrics['r2'] = float(r2_score(y_test, y_pred))
                else:
                    self.metrics['rmse'] = None
                    self.metrics['r2'] = None
            else:
                self.metrics['rmse'] = None
                self.metrics['r2'] = None
            
            self.is_fitted = True
        except Exception as e:
            logger.error(f"Error fitting models: {e}")
            self.metrics['rmse'] = None
            self.metrics['r2'] = None
    
    def _calculate_basic_overall_rating(self, features: np.ndarray) -> float:
        """Calculate basic overall rating from features"""
        # Weighted average of key metrics
        weights = [0.2, 0.2, 0.1, 0.1, 0.1, 0.05, 0.1, 0.05, 0.05, 0.05, 0.0, 0.0]
        weighted_sum = np.sum(features[:12] * weights)
        
        # Scale to 40-99 range (MLB The Show style)
        return np.clip(40 + weighted_sum * 0.5, 40, 99)
    
    def get_similar_players(self, db: Session, player_id: int, k: int = 5) -> List[Dict]:
        start = time.time()
        """Find similar MLB players using KNN"""
        if not self.is_fitted:
            self.fit_models(db)
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return []
        ptype = self.get_player_type(player)
        features = None
        scaler = None
        knn_model = None
        player_ids = None
        if ptype == 'pitcher':
            if not hasattr(self, 'scaler_pit') or not hasattr(self, 'knn_model_pit') or not hasattr(self, 'pitcher_ids'):
                return []
            scaler = self.scaler_pit
            knn_model = self.knn_model_pit
            player_ids = self.pitcher_ids
            features = self.extract_player_features(db, int(player_id), mode='pitching')
        elif ptype in ('position_player', 'dh'):
            if not hasattr(self, 'scaler_hit') or not hasattr(self, 'knn_model_hit') or not hasattr(self, 'hitter_ids'):
                return []
            scaler = self.scaler_hit
            knn_model = self.knn_model_hit
            player_ids = self.hitter_ids
            features = self.extract_player_features(db, int(player_id), mode='hitting')
        else:
            return []
        if features is None or scaler is None or knn_model is None or player_ids is None:
            return []
        try:
            features_scaled = scaler.transform(features["normalized"].reshape(1, -1))
            distances, indices = knn_model.kneighbors(features_scaled, n_neighbors=min(k+1, len(player_ids)))
        except Exception as e:
            logger.error(f"Error in get_similar_players: {e}")
            return []
        similar_players = []
        today = datetime.date.today().isoformat()
        for i, (distance, idx) in enumerate(zip(distances[0][1:], indices[0][1:])):  # Skip first (self)
            similar_player_id = player_ids[idx]
            player = db.query(Player).filter(Player.id == similar_player_id).first()
            if player:
                similar_players.append({
                    'id': i,
                    'mlb_player_id': similar_player_id,
                    'mlb_player_name': player.full_name,
                    'mlb_player_team': player.team,
                    'similarity_score': 1.0 / (1.0 + distance),
                    'comparison_reason': 'Statistical similarity',
                    'comp_date': today
                })
        elapsed = time.time() - start
        print(f"[PERF] get_similar_players for player {player_id} took {elapsed:.2f}s")
        return similar_players
    
    def get_player_type(self, player) -> str:
        """
        Classify player as 'pitcher', 'position_player', or 'two_way' using only primary_position.
        - If primary_position is exactly 'Pitcher', classify as pitcher.
        - If primary_position contains 'Pitcher' and at least one other position (including DH), classify as two_way.
        - Otherwise, classify as position_player.
        """
        primary_position = (getattr(player, 'primary_position', '') or '').strip()
        if not primary_position:
            return 'position_player'
        pos_str = primary_position.lower()
        positions = [p.strip() for p in re.split(r',| and ', pos_str) if p.strip()]
        # Pitcher only
        if len(positions) == 1 and positions[0] == 'pitcher':
            return 'pitcher'
        # Two-way: must have pitcher and at least one other position
        if 'pitcher' in positions and len(positions) > 1:
            return 'two_way'
        # Otherwise, position player
        return 'position_player'
    
    def safe_tool(self, *args):
        arr = np.array(args, dtype=float)
        arr = arr[~np.isnan(arr)]
        if len(arr) == 0:
            return 40.0
        return float(np.mean(arr))

    def _get_similar_player_growth(self, db: Session, player_id: int, mode: str, k: int = 5) -> Optional[float]:
        similar_players = self.get_similar_players(db, player_id, k=k)
        growths = []
        for comp in similar_players:
            comp_id = comp.get('mlb_player_id')
            if not comp_id:
                continue
            overalls = self._get_recent_overalls(db, comp_id, mode, n_seasons=5)
            if overalls and len(overalls) >= 3:
                growth = max(overalls) - overalls[0]
                if growth > 0:
                    growths.append(growth)
        if growths:
            avg_growth = float(np.mean(growths))
            return avg_growth
        return None

    def _calculate_trend_potential(self, overalls: list, current_overall: float, scaling: float = 2.0, db: Optional[Session] = None, player_id: Optional[int] = None, mode: Optional[str] = None) -> float:
        if not overalls or len(overalls) < 2:
            trend = 0
            if db is not None and player_id is not None and mode is not None:
                avg_growth = self._get_similar_player_growth(db, player_id, mode)
                if avg_growth is not None:
                    potential = min(99, current_overall + avg_growth)
                    return potential
        else:
            trend = overalls[-1] - overalls[0]
            if trend < 0:
                # Use max overall if trend is negative
                potential = max(overalls + [current_overall])
                return potential
        potential = min(99, current_overall + scaling * trend)
        return potential

    def _get_recent_overalls(self, db, player_id: int, mode: str, n_seasons: int = 3) -> list:
        if mode == 'hitting':
            stats = db.query(StandardBattingStat).filter(StandardBattingStat.player_id == player_id).order_by(StandardBattingStat.season.asc()).all()
        elif mode == 'pitching':
            stats = db.query(StandardPitchingStat).filter(StandardPitchingStat.player_id == player_id).order_by(StandardPitchingStat.season.asc()).all()
        else:
            return []
        overalls = []
        for stat in stats[-n_seasons:]:
            season = getattr(stat, 'season', None)
            feats = self.extract_player_features(db, player_id, mode=mode, season=season)
            if feats is None:
                continue
            norm = feats["normalized"]
            if mode == 'hitting':
                contact = np.mean([norm[0], norm[1], norm[2], norm[3], norm[4]])
                power = np.mean([norm[5], norm[6], norm[7], norm[8]])
                discipline = np.mean([norm[9], norm[10], norm[11], norm[12]])
                vision = np.mean([norm[9], norm[10], norm[0]])
                fielding = norm[15] if len(norm) > 17 else 40.0
                arm_strength = norm[18] if len(norm) > 19 else 40.0
                arm_accuracy = norm[18] if len(norm) > 18 else 40.0
                speed = norm[13] if len(norm) > 14 else 40.0
                stealing = norm[13] if len(norm) > 14 else 40.0
                tool_vals = [float(x) if x is not None else 40.0 for x in [contact, power, discipline, vision, fielding, arm_strength, arm_accuracy, speed, stealing]]
                top_tools = sorted(tool_vals, reverse=True)[:4]
                overall = np.mean(top_tools)
            elif mode == 'pitching':
                k_rating = norm[0] if len(norm) > 0 else 40.0
                bb_rating = 100 - (norm[1] if len(norm) > 1 else 40.0)
                gb_rating = norm[19] if len(norm) > 19 else 40.0
                hr_rating = 100 - (norm[2] if len(norm) > 2 else 40.0)
                command_rating = float(np.mean([norm[3], norm[4], norm[5], norm[20], norm[21], norm[22], norm[23], norm[7], norm[9]]))
                tool_vals = [float(x) if x is not None else 40.0 for x in [k_rating, bb_rating, gb_rating, hr_rating, command_rating]]
                top_tools = sorted(tool_vals, reverse=True)[:3]
                overall = np.mean(top_tools)
            else:
                overall = 40.0
            overalls.append(overall)
        return overalls[-n_seasons:]

    def _get_recent_overalls_with_seasons(self, db, player_id: int, mode: str, n_seasons: int = 5) -> list:
        """
        Fetch the last n_seasons' (season, overall) for a player (batting or pitching), oldest to newest.
        """
        if mode == 'hitting':
            stats = db.query(StandardBattingStat).filter(StandardBattingStat.player_id == player_id).order_by(StandardBattingStat.season.asc()).all()
        elif mode == 'pitching':
            stats = db.query(StandardPitchingStat).filter(StandardPitchingStat.player_id == player_id).order_by(StandardPitchingStat.season.asc()).all()
        else:
            return []
        results = []
        for stat in stats[-n_seasons:]:
            season = getattr(stat, 'season', None)
            feats = self.extract_player_features(db, player_id, mode=mode, season=season)
            if feats is None:
                continue
            norm = feats["normalized"]
            if mode == 'hitting':
                contact = np.mean([norm[0], norm[1], norm[2], norm[3], norm[4]])
                power = np.mean([norm[5], norm[6], norm[7], norm[8]])
                discipline = np.mean([norm[9], norm[10], norm[11], norm[12]])
                vision = np.mean([norm[9], norm[10], norm[0]])
                fielding = norm[15] if len(norm) > 17 else 40.0
                arm_strength = norm[18] if len(norm) > 19 else 40.0
                arm_accuracy = norm[18] if len(norm) > 18 else 40.0
                speed = norm[13] if len(norm) > 14 else 40.0
                stealing = norm[13] if len(norm) > 14 else 40.0
                tool_vals = [float(x) if x is not None else 40.0 for x in [contact, power, discipline, vision, fielding, arm_strength, arm_accuracy, speed, stealing]]
                top_tools = sorted(tool_vals, reverse=True)[:4]
                overall = np.mean(top_tools)
            elif mode == 'pitching':
                k_rating = norm[0] if len(norm) > 0 else 40.0
                bb_rating = 100 - (norm[1] if len(norm) > 1 else 40.0)
                gb_rating = norm[19] if len(norm) > 19 else 40.0
                hr_rating = 100 - (norm[2] if len(norm) > 2 else 40.0)
                command_rating = float(np.mean([norm[3], norm[4], norm[5], norm[20], norm[21], norm[22], norm[23], norm[7], norm[9]]))
                tool_vals = [float(x) if x is not None else 40.0 for x in [k_rating, bb_rating, gb_rating, hr_rating, command_rating]]
                top_tools = sorted(tool_vals, reverse=True)[:3]
                overall = np.mean(top_tools)
            else:
                overall = 40.0
            results.append({"season": season, "overall": overall})
        return results[-n_seasons:]

    def calculate_mlb_show_ratings(self, db: Session, player_id: int) -> Dict:
        if not hasattr(self, 'pca_weights_hit') or not hasattr(self, 'pca_weights_pit'):
            self.fit_models(db)
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return {}
        ptype = self.get_player_type(player)
        feats_dict = self.extract_player_features(db, player_id)
        if feats_dict is None:
                return {}
        feats = feats_dict["normalized"]
        present = feats_dict.get("present", [True]*len(feats))
        # Only use present features for overall calculation
        def f(idx, default=40.0):
            try:
                val = float(np.clip(feats[idx], 0, 99)) if present[idx] else None
                return val if val is not None else default
            except Exception:
                return default
        # Hitting ratings (indices based on feature vector)
        grades = {
            'contact_left': f(0),
            'contact_right': f(0),
            'power_left': f(5),
            'power_right': f(5),
            'vision': f(9),
            'discipline': f(10),
            'fielding': f(15),
            'arm_strength': f(18),
            'arm_accuracy': f(18),
            'speed': f(13),
            'stealing': f(13),
        }
        # --- Weighted mean for overall ---
        if ptype == 'pitcher':
            # Pitcher weights
            weights = np.array([
                0.2,  # k_rating (0)
                0.2,  # bb_rating (1)
                0.1,  # gb_rating (19)
                0.1,  # hr_rating (2)
                0.2,  # command_rating (mean of 3,4,5,20,21,22,23,7,9)
                0.05, # fielding (15)
                0.05, # arm_strength (18)
                0.05, # speed (13)
                0.05, # stealing (13)
            ])
            # Feature vector for pitcher overall
            pitcher_feats = np.array([
                f(0),
                100 - (f(1) if f(1) is not None else 40.0),
                f(19),
                100 - (f(2) if f(2) is not None else 40.0),
                float(np.mean([x for x in [f(3), f(4), f(5), f(20), f(21), f(22), f(23), f(7), f(9)] if x is not None])),
                f(15),
                f(18),
                f(13),
                f(13),
            ])
            overall_rating = float(np.clip(np.average(pitcher_feats, weights=weights), 0, 99))
        elif ptype == 'two_way':
            # Compute both hitting and pitching overalls, then average
            # Hitting weights
            hit_weights = np.array([0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.05,0.05,0.1,0.05])
            hit_feats = np.array([
                f(0), f(0), f(5), f(5), f(9), f(10), f(15), f(18), f(18), f(13), f(13)
            ])
            hitting_overall = float(np.clip(np.average(hit_feats, weights=hit_weights), 0, 99))
            # Pitching weights (same as above)
            pit_weights = np.array([
                0.2, 0.2, 0.1, 0.1, 0.2, 0.05, 0.05, 0.05, 0.05
            ])
            pit_feats = np.array([
                f(0), 100 - (f(1) if f(1) is not None else 40.0), f(19), 100 - (f(2) if f(2) is not None else 40.0), float(np.mean([x for x in [f(3), f(4), f(5), f(20), f(21), f(22), f(23), f(7), f(9)] if x is not None])), f(15), f(18), f(13), f(13)
            ])
            pitching_overall = float(np.clip(np.average(pit_feats, weights=pit_weights), 0, 99))
            overall_rating = float(np.clip((hitting_overall + pitching_overall) / 2, 0, 99))
        else:
            # Position player weights
            weights = np.array([0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.05,0.05,0.1,0.05])
            feats_vec = np.array([
                f(0), f(0), f(5), f(5), f(9), f(10), f(15), f(18), f(18), f(13), f(13)
            ])
            overall_rating = float(np.clip(np.average(feats_vec, weights=weights), 0, 99))
        # --- Potential: project from historical overalls ---
        historical = self._get_recent_overalls(db, player_id, 'hitting' if ptype != 'pitcher' else 'pitching', n_seasons=5)
        if historical and len(historical) > 1:
            trend = (historical[-1] - historical[0]) / (len(historical) - 1)
            potential_rating = float(np.clip(historical[-1] + trend * 2, 0, 99))
        else:
            potential_rating = overall_rating
        # --- Confidence: stddev of features, scaled to 0-100 ---
        confidence_score = float(np.clip(100 - np.std(feats), 0, 100))
        # Pitcher-specific ratings
        if ptype == 'pitcher':
            grades['k_rating'] = f(0)
            grades['bb_rating'] = 100 - (f(1) if f(1) is not None else 40.0)
            grades['gb_rating'] = f(19)
            grades['hr_rating'] = 100 - (f(2) if f(2) is not None else 40.0)
            grades['command_rating'] = float(np.mean([x for x in [f(3), f(4), f(5), f(20), f(21), f(22), f(23), f(7), f(9)] if x is not None]))
            historical_overalls = self._get_recent_overalls_with_seasons(db, player_id, 'pitching', n_seasons=5)
            return {
                'grades': grades,
                'player_type': ptype,
                'overall_rating': overall_rating,
                'potential_rating': potential_rating,
                'confidence_score': confidence_score,
                'historical_overalls': historical_overalls,
            }
        # If two-way, return both hitting and pitching ratings
        if ptype == 'two_way':
            feats_hit = self.extract_player_features(db, player_id, mode='hitting')
            feats_pit = self.extract_player_features(db, player_id, mode='pitching')
            def f2(feats, idx, default=40.0):
                try:
                    return float(np.clip(feats["normalized"][idx], 0, 99))
                except Exception:
                    return default
            hitting_history = self._get_recent_overalls_with_seasons(db, player_id, 'hitting', n_seasons=5)
            pitching_history = self._get_recent_overalls_with_seasons(db, player_id, 'pitching', n_seasons=5)
            grades = {
                'hitting': {
                    'contact_left': f2(feats_hit, 0),
                    'contact_right': f2(feats_hit, 0),
                    'power_left': f2(feats_hit, 5),
                    'power_right': f2(feats_hit, 5),
                    'vision': f2(feats_hit, 9),
                    'discipline': f2(feats_hit, 10),
                    'fielding': f2(feats_hit, 15),
                    'arm_strength': f2(feats_hit, 18),
                    'arm_accuracy': f2(feats_hit, 18),
                    'speed': f2(feats_hit, 13),
                    'stealing': f2(feats_hit, 13),
                    'overall_rating': float(np.clip(np.mean(feats_hit["normalized"]), 0, 99)) if feats_hit else 40.0,
                    'potential_rating': float(np.clip(np.max(feats_hit["normalized"]), 0, 99)) if feats_hit else 40.0,
                    'confidence_score': float(np.clip(100 - np.std(feats_hit["normalized"]), 0, 100)) if feats_hit else 0.0,
                    'player_type': 'position_player',
                    'historical_overalls': hitting_history,
                },
                'pitching': {
                    'k_rating': f2(feats_pit, 0),
                    'bb_rating': 100 - (f2(feats_pit, 1) if f2(feats_pit, 1) is not None else 40.0),
                    'gb_rating': f2(feats_pit, 19),
                    'hr_rating': 100 - (f2(feats_pit, 2) if f2(feats_pit, 2) is not None else 40.0),
                    'command_rating': float(np.mean([x for x in [f2(feats_pit, 3), f2(feats_pit, 4), f2(feats_pit, 5), f2(feats_pit, 20), f2(feats_pit, 21), f2(feats_pit, 22), f2(feats_pit, 23), f2(feats_pit, 7), f2(feats_pit, 9)] if x is not None])),
                    'overall_rating': float(np.clip(np.mean(feats_pit["normalized"]), 0, 99)) if feats_pit else 40.0,
                    'potential_rating': float(np.clip(np.max(feats_pit["normalized"]), 0, 99)) if feats_pit else 40.0,
                    'confidence_score': float(np.clip(100 - np.std(feats_pit["normalized"]), 0, 100)) if feats_pit else 0.0,
                    'player_type': 'pitcher',
                    'historical_overalls': pitching_history,
                },
            }
            return {
                'grades': grades,
                'player_type': 'two_way',
                'overall_rating': overall_rating,
                'potential_rating': potential_rating,
                'confidence_score': confidence_score,
            }
        # For position players (not pitcher or two_way), return grades
        historical_overalls = self._get_recent_overalls_with_seasons(db, player_id, 'hitting', n_seasons=5)
        return {
            'grades': grades,
            'player_type': ptype,
            'overall_rating': overall_rating,
            'potential_rating': potential_rating,
            'confidence_score': confidence_score,
            'historical_overalls': historical_overalls,
        }

    def store_level_weights(self, db: Session):
        """Persist the current data_driven_level_weights to the DB."""
        lw = db.query(LevelWeights).first()
        if lw and isinstance(getattr(lw, 'weights_json', None), dict):
            setattr(lw, 'weights_json', self.data_driven_level_weights)
            setattr(lw, 'last_updated', datetime.datetime.utcnow())
        else:
            lw = LevelWeights(weights_json=self.data_driven_level_weights)
            db.add(lw)
        db.commit()

    def load_level_weights(self, db: Session):
        """Load level weights from the DB if present."""
        lw = db.query(LevelWeights).order_by(LevelWeights.last_updated.desc()).first()
        if lw is not None and isinstance(getattr(lw, 'weights_json', None), dict):
            self.data_driven_level_weights = lw.weights_json
            return True
        return False

    def _hof_probability(self, projected_career_war: float, player_type: str = "position_player") -> float:
        # Thresholds based on historical HOF inductees
        if player_type == "pitcher":
            w0 = 50
            k = 0.18
        else:
            w0 = 60
            k = 0.20
        # Logistic curve
        prob = 1.0 / (1.0 + np.exp(-k * (projected_career_war - w0)))
        # Clamp to [0, 0.99]
        return float(np.clip(prob, 0, 0.99))

    def predict_mlb_success(self, db, player_id: int):
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return None
        ptype = self.get_player_type(player)
        level = getattr(player, 'level', None)
        age = getattr(player, 'age', None) or 24  # fallback if missing
        is_mlb = (level == 'MLB')
        # --- Career WAR calculation ---
        def get_batting_career_war():
            war = 0.0
            seasons = set(
                row.season for row in db.query(StandardBattingStat)
                .filter(StandardBattingStat.player_id == player_id, StandardBattingStat.level == 'MLB').all()
                if row.season is not None
            )
            for row in db.query(StandardBattingStat).filter(StandardBattingStat.player_id == player_id, StandardBattingStat.level == 'MLB').all():
                if getattr(row, 'season', None) in seasons:
                    war += getattr(row, 'war', 0.0) or 0.0
            return war
        def get_pitching_career_war():
            war = 0.0
            pitching_seasons = set(
                row.season for row in db.query(StandardPitchingStat)
                .filter(StandardPitchingStat.player_id == player_id, StandardPitchingStat.level == 'MLB').all()
                if row.season is not None
            )
            for row in db.query(StandardPitchingStat).filter(StandardPitchingStat.player_id == player_id, StandardPitchingStat.level == 'MLB').all():
                if getattr(row, 'season', None) in pitching_seasons:
                    war += getattr(row, 'war', 0.0) or 0.0
            return war
        def get_mlb_debut_year():
            # Find the earliest MLB season in batting or pitching
            seasons = [row.season for row in db.query(StandardBattingStat).filter(StandardBattingStat.player_id == player_id, StandardBattingStat.level == 'MLB').all() if row.season]
            seasons += [row.season for row in db.query(StandardPitchingStat).filter(StandardPitchingStat.player_id == player_id, StandardPitchingStat.level == 'MLB').all() if row.season]
            if seasons:
                return min(seasons)
            return None
        batting_career_war = get_batting_career_war()
        pitching_career_war = get_pitching_career_war()
        career_war = batting_career_war + pitching_career_war
        debut_year = get_mlb_debut_year()
        # --- Similar players for comps ---
        similar = self.get_similar_players(db, player_id, k=5)
        def get_similar_career_wars():
            wars = []
            for comp in similar:
                comp_id = comp.get('mlb_player_id')
                if not comp_id:
                    continue
                # For each comp, sum MLB WAR (batting + pitching) using MLB seasons only
                # Batting
                mlb_bat_seasons = set(
                    row.season for row in db.query(StandardBattingStat)
                    .filter(StandardBattingStat.player_id == comp_id, StandardBattingStat.level == 'MLB').all()
                    if row.season is not None
                )
                bwar = 0.0
                for row in db.query(StandardBattingStat).filter(StandardBattingStat.player_id == comp_id, StandardBattingStat.level == 'MLB').all():
                    if getattr(row, 'season', None) in mlb_bat_seasons:
                        bwar += getattr(row, 'war', 0.0) or 0.0
                # Pitching
                mlb_pit_seasons = set(
                    row.season for row in db.query(StandardPitchingStat)
                    .filter(StandardPitchingStat.player_id == comp_id, StandardPitchingStat.level == 'MLB').all()
                    if row.season is not None
                )
                pwar = 0.0
                for row in db.query(StandardPitchingStat).filter(StandardPitchingStat.player_id == comp_id, StandardPitchingStat.level == 'MLB').all():
                    if getattr(row, 'season', None) in mlb_pit_seasons:
                        pwar += getattr(row, 'war', 0.0) or 0.0
                wars.append(bwar + pwar)
            return wars
        comp_wars = get_similar_career_wars()
        # --- ETA calculation ---
        comp_ages = []
        for comp in similar:
            comp_id = comp.get('mlb_player_id')
            if not comp_id:
                continue
            comp_debut = None
            for row in db.query(StandardBattingStat).filter(StandardBattingStat.player_id == comp_id, StandardBattingStat.level == 'MLB').all():
                if row.season:
                    comp_debut = row.season
                    break
            for row in db.query(StandardPitchingStat).filter(StandardPitchingStat.player_id == comp_id, StandardPitchingStat.level == 'MLB').all():
                if row.season:
                    comp_debut = row.season
                    break
            comp_player = db.query(Player).filter(Player.id == comp_id).first()
            comp_age = getattr(comp_player, 'age', None)
            if comp_debut and comp_age:
                comp_ages.append(comp_debut - (comp_age or 24))
        if comp_ages:
            eta_mlb = age + int(np.mean(comp_ages))
        else:
            eta_mlb = age + 2
        # Projected career WAR: blended approach considering current performance and comps
        comp_average_war = float(np.mean(comp_wars)) if comp_wars else 2.0
        
        # Calculate age-adjusted projection
        if is_mlb and career_war > 0:
            # For MLB players with existing WAR, blend current performance with comp projection
            # Weight current WAR more heavily for younger players, comp average more for older players
            age_factor = min(1.0, max(0.0, (age - 20) / 15))  # 0 at age 20, 1 at age 35+
            current_weight = 0.7 * (1 - age_factor)  # Higher weight for younger players
            comp_weight = 0.3 + (0.4 * age_factor)   # Higher weight for older players
            
            # Ensure projection is at least current WAR (can't go backwards)
            blended_projection = max(
                career_war,
                (current_weight * career_war) + (comp_weight * comp_average_war)
            )
            
            # Add future WAR projection based on age and current performance
            if age < 30:
                # Younger players: project additional WAR based on current rate and remaining prime years
                years_in_mlb = 2025 - int(debut_year) if debut_year else 1
                war_per_year = career_war / years_in_mlb if years_in_mlb > 0 else 2.0
                remaining_prime_years = max(0, 30 - age)
                future_war = war_per_year * remaining_prime_years * 0.8  # 80% of current rate for future
                projected_career_war = career_war + future_war
            else:
                # Older players: use blended projection with some future WAR
                future_war = max(0, (35 - age) * 1.0)  # Conservative future projection
                projected_career_war = blended_projection + future_war
        else:
            # For prospects or players without MLB WAR, use comp average with some upward adjustment
            projected_career_war = comp_average_war * 1.2  # 20% upward adjustment for prospects
        
        ceiling = max(comp_wars) if comp_wars else projected_career_war * 1.5
        floor = min(comp_wars) if comp_wars else projected_career_war * 0.5
        
        # --- Ceiling/Floor Comparison Labels ---
        def get_career_outcome_label(war: float) -> str:
            if war >= 70:
                return "Hall of Fame Candidate"
            elif war >= 50:
                return "All-Star Level"
            elif war >= 30:
                return "MLB Regular"
            elif war >= 15:
                return "MLB Role Player"
            elif war >= 5:
                return "MLB Bench Player"
            elif war >= 0:
                return "Quad-A Player"
            else:
                return "Minor League Player"
        
        ceiling_label = get_career_outcome_label(ceiling)
        floor_label = get_career_outcome_label(floor)
        ceiling_comparison = ceiling_label
        floor_comparison = floor_label
        if comp_wars and similar:
            # Find comp with max/min WAR
            max_idx = comp_wars.index(ceiling)
            min_idx = comp_wars.index(floor)
            if 0 <= max_idx < len(similar):
                ceiling_name = similar[max_idx].get('mlb_player_name')
                if ceiling_name:
                    ceiling_comparison = f"{ceiling_label} ({ceiling_name}, {ceiling:.1f} WAR)"
            if 0 <= min_idx < len(similar):
                floor_name = similar[min_idx].get('mlb_player_name')
                if floor_name:
                    floor_comparison = f"{floor_label} ({floor_name}, {floor:.1f} WAR)"
        # --- Risk factor ---
        spread = ceiling - floor
        risk_factor = "Low"
        if spread > 20:
            risk_factor = "High"
        elif spread > 10:
            risk_factor = "Medium"
        # For non-MLB, bump risk if level is low
        if not is_mlb:
            if level in ("A", "A+", "Rk", "HS", "NCAA"):
                risk_factor = "High"
            elif level in ("AA",):
                if risk_factor == "Low":
                    risk_factor = "Medium"
        # --- Probability logic ---
        # Dummy logic for now; replace with your model
        if is_mlb:
            hof_prob = self._hof_probability(projected_career_war, ptype)
            result = {
                'hall_of_fame_probability': hof_prob,
                'debut_year': debut_year,
                'current_career_war': career_war,
                'projected_career_war': projected_career_war,
                'ceiling': ceiling,
                'floor': floor,
                'ceiling_comparison': ceiling_comparison,
                'floor_comparison': floor_comparison,
                'risk_factor': risk_factor,
                'similar': similar,
            }
        else:
            mlb_debut_prob = 0.7  # Dummy: replace with your model
            result = {
                'mlb_debut_probability': mlb_debut_prob,
                'eta_mlb': eta_mlb,
                'projected_career_war': projected_career_war,
                'ceiling': ceiling,
                'floor': floor,
                'ceiling_comparison': ceiling_comparison,
                'floor_comparison': floor_comparison,
                'risk_factor': risk_factor,
                'similar': similar,
            }
        return result

ml_service = BaseballMLService()