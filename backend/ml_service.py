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
import re

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
        
    def compute_stat_normalization(self, db: Session):
        """Compute min/max (or percentiles) for each stat from MLB data and cache them."""
        players = db.query(models.Player).all()
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
        bat = db.query(models.StandardBattingStat).filter(models.StandardBattingStat.player_id == player_id).order_by(models.StandardBattingStat.season.desc()).first()
        pit = db.query(models.StandardPitchingStat).filter(models.StandardPitchingStat.player_id == player_id).order_by(models.StandardPitchingStat.season.desc()).first()
        stat = bat if (bat and (not pit or bat.season >= pit.season)) else pit
        if stat and hasattr(stat, 'team') and stat.team:
            team = stat.team.lower()
            if team in ["yankees", "dodgers", "red sox", "cubs", "braves", "astros", "mets", "giants", "padres", "cardinals"]:
                return "MLB"
            elif team in ["rainiers", "stripers", "ironpigs", "sounds", "bisons", "chihuahuas", "express", "river cats", "isotopes", "bulls"]:
                return "AAA"
            # Add more mappings as needed
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
    
    def compute_level_weights_from_data(self, db: Session):
        """Compute data-driven level weights by analyzing performance differences between levels"""
        try:
            print("[ML] Computing data-driven level weights...")
            
            # Get all players with stats
            players = db.query(models.Player).all()
            
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
                bat_stats = db.query(models.StandardBattingStat).filter(
                    models.StandardBattingStat.player_id == player.id
                ).order_by(models.StandardBattingStat.season.desc()).first()
                
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
                pit_stats = db.query(models.StandardPitchingStat).filter(
                    models.StandardPitchingStat.player_id == player.id
                ).order_by(models.StandardPitchingStat.season.desc()).first()
                
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
                    if stats_dict['ip'] > 10:
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
            
        except Exception as e:
            logger.error(f"Error computing level weights: {e}")
            # Fall back to default weights
            self.data_driven_level_weights = {
                'MLB': 1.0, 'AAA': 0.8, 'AA': 0.6, 'A+': 0.4, 'A': 0.3, 'Rk': 0.2
            }
    
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
    
    def extract_player_features(self, db: Session, player_id: int, mode: str = 'all') -> Optional[dict]:
        """Extract feature vector for a player, split by mode: 'hitting', 'pitching', or 'all' (default)."""
        try:
            player = db.query(models.Player).filter(models.Player.id == player_id).first()
            if not player:
                return None
            
            # Get the player's level for weighting
            player_level = getattr(player, 'level', 'MLB')
            level_factor = self._get_level_factor(player_level)
            
            # Get latest stats from all canonical tables
            adv_bat = db.query(models.AdvancedBattingStat).filter(models.AdvancedBattingStat.player_id == player_id).order_by(models.AdvancedBattingStat.season.desc()).first()
            val_bat = db.query(models.ValueBattingStat).filter(models.ValueBattingStat.player_id == player_id).order_by(models.ValueBattingStat.season.desc()).first()
            std_bat = db.query(models.StandardBattingStat).filter(models.StandardBattingStat.player_id == player_id).order_by(models.StandardBattingStat.season.desc()).first()
            adv_pit = db.query(models.AdvancedPitchingStat).filter(models.AdvancedPitchingStat.player_id == player_id).order_by(models.AdvancedPitchingStat.season.desc()).first()
            val_pit = db.query(models.ValuePitchingStat).filter(models.ValuePitchingStat.player_id == player_id).order_by(models.ValuePitchingStat.season.desc()).first()
            std_pit = db.query(models.StandardPitchingStat).filter(models.StandardPitchingStat.player_id == player_id).order_by(models.StandardPitchingStat.season.desc()).first()
            std_field = db.query(models.StandardFieldingStat).filter(models.StandardFieldingStat.player_id == player_id).order_by(models.StandardFieldingStat.season.desc()).first()
            
            def safe_float(val):
                try:
                    return float(val)
                except (TypeError, ValueError):
                    return 0.0
            
            # Helper function to apply level weighting to stats
            def level_weighted_stat(val, is_percentage=False):
                """Apply level weighting to a stat value"""
                raw_val = safe_float(val)
                if raw_val == 0:
                    return 0.0
                
                # For percentages (like BA, OBP, SLG), we need to be more careful
                if is_percentage:
                    # For percentages, we scale the difference from league average
                    # MLB average BA is ~0.250, so we scale the difference
                    if raw_val > 0.5:  # Likely a percentage like BA, OBP, SLG
                        # Scale the difference from 0.250 (MLB average BA)
                        diff_from_avg = raw_val - 0.250
                        weighted_diff = diff_from_avg * level_factor
                        return 0.250 + weighted_diff
                    else:
                        # For other percentages, scale directly
                        return raw_val * level_factor
                else:
                    # For counting stats (HR, RBI, etc.), scale by level factor
                    return raw_val * level_factor
            
            # --- Feature sets with level weighting ---
            hitting_feats = [
                level_weighted_stat(getattr(std_bat, 'ba', None), is_percentage=True),
                level_weighted_stat(getattr(std_bat, 'obp', None), is_percentage=True),
                level_weighted_stat(getattr(adv_bat, 'ev', None)),
                level_weighted_stat(getattr(adv_bat, 'hardh_pct', None), is_percentage=True),
                level_weighted_stat(getattr(adv_bat, 'ld_pct', None), is_percentage=True),
                level_weighted_stat(getattr(std_bat, 'slg', None), is_percentage=True),
                level_weighted_stat(getattr(adv_bat, 'iso', None), is_percentage=True),
                level_weighted_stat(getattr(adv_bat, 'barrel_pct', None), is_percentage=True),
                level_weighted_stat(getattr(std_bat, 'hr', None)),
                level_weighted_stat(getattr(adv_bat, 'bb_pct', None), is_percentage=True),
                level_weighted_stat(getattr(adv_bat, 'so_pct', None), is_percentage=True),
                level_weighted_stat(getattr(std_bat, 'bb', None)),
                level_weighted_stat(getattr(std_bat, 'so', None)),
                level_weighted_stat(getattr(std_bat, 'sb', None)),
                level_weighted_stat(getattr(val_bat, 'rbaser', None)),
            ]
            fielding_feats = [
                level_weighted_stat(getattr(std_field, 'fld_pct', None), is_percentage=True),
                level_weighted_stat(getattr(std_field, 'rdrs', None)),
                level_weighted_stat(getattr(std_field, 'rtot', None)),
                level_weighted_stat(getattr(std_field, 'a', None)),
                level_weighted_stat(getattr(std_field, 'dp', None)),
            ]
            pitching_feats = [
                level_weighted_stat(getattr(adv_pit, 'k_pct', None), is_percentage=True),
                level_weighted_stat(getattr(adv_pit, 'bb_pct', None), is_percentage=True),
                level_weighted_stat(getattr(adv_pit, 'hr_pct', None), is_percentage=True),
                level_weighted_stat(getattr(std_pit, 'era', None)),
                level_weighted_stat(getattr(std_pit, 'fip', None)),
                level_weighted_stat(getattr(std_pit, 'whip', None)),
                level_weighted_stat(getattr(std_pit, 'era_plus', None)),
                level_weighted_stat(getattr(val_pit, 'war', None)),
                level_weighted_stat(getattr(val_pit, 'waa', None)),
                level_weighted_stat(getattr(val_pit, 'raa', None)),
                level_weighted_stat(getattr(std_pit, 'so', None)),
                level_weighted_stat(getattr(std_pit, 'bb', None)),
                level_weighted_stat(getattr(std_pit, 'ip', None)),
                level_weighted_stat(getattr(std_pit, 'gs', None)),
                level_weighted_stat(getattr(std_pit, 'so9', None)),
                level_weighted_stat(getattr(std_pit, 'bb9', None)),
                level_weighted_stat(getattr(std_pit, 'hr9', None)),
                level_weighted_stat(getattr(std_pit, 'h9', None)),
                level_weighted_stat(getattr(adv_pit, 'babip', None), is_percentage=True),
                level_weighted_stat(getattr(adv_pit, 'lob_pct', None), is_percentage=True),
                level_weighted_stat(getattr(adv_pit, 'era_minus', None)),
                level_weighted_stat(getattr(adv_pit, 'fip_minus', None)),
                level_weighted_stat(getattr(adv_pit, 'xfip_minus', None)),
                level_weighted_stat(getattr(adv_pit, 'siera', None)),
                level_weighted_stat(getattr(val_pit, 'wpa', None)),
                level_weighted_stat(getattr(val_pit, 're24', None)),
                level_weighted_stat(getattr(val_pit, 'cwpa', None)),
            ]
            
            # Compose feature sets
            if mode == 'hitting':
                feats = np.array(hitting_feats + fielding_feats + [level_factor * 100, 1.0])
            elif mode == 'pitching':
                feats = np.array(pitching_feats + fielding_feats + [level_factor * 100, 1.0])
            else:
                feats = np.array(hitting_feats + fielding_feats + pitching_feats + [level_factor * 100, 1.0])
            
            normed = self._normalize_features(feats)
            return {"raw": feats, "normalized": normed, "level": player_level, "level_factor": level_factor}
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
            # Compute data-driven level weights first
            self.compute_level_weights_from_data(db)
            
            # Only use MLB players for training the comparison models
            players = db.query(models.Player).filter(models.Player.level == 'MLB').all()
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
        """Find similar MLB players using KNN"""
        if not self.is_fitted:
            self.fit_models(db)
        player = db.query(models.Player).filter(models.Player.id == player_id).first()
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
            player = db.query(models.Player).filter(models.Player.id == similar_player_id).first()
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
            print(f"[DEBUG] Similar player growths for player {player_id} ({mode}): {growths}, avg_growth={avg_growth}")
            return avg_growth
        print(f"[DEBUG] No similar player growth found for player {player_id} ({mode})")
        return None

    def _calculate_trend_potential(self, overalls: list, current_overall: float, scaling: float = 2.0, db: Optional[Session] = None, player_id: Optional[int] = None, mode: Optional[str] = None) -> float:
        print(f"[DEBUG] _calculate_trend_potential: player_id={player_id}, mode={mode}, overalls={overalls}, current_overall={current_overall}")
        if not overalls or len(overalls) < 2:
            trend = 0
            if db is not None and player_id is not None and mode is not None:
                avg_growth = self._get_similar_player_growth(db, player_id, mode)
                if avg_growth is not None:
                    potential = min(99, current_overall + avg_growth)
                    print(f"[DEBUG] Only one season. Using similar player avg_growth={avg_growth}. potential={potential}")
                    return potential
        else:
            trend = overalls[-1] - overalls[0]
        potential = min(99, current_overall + scaling * trend)
        print(f"[DEBUG] Trend={trend}, scaling={scaling}, potential={potential}")
        return potential

    def _get_recent_overalls(self, db, player_id: int, mode: str, n_seasons: int = 3) -> list:
        """
        Fetch the last n_seasons' overall ratings for a player (batting or pitching), oldest to newest.
        """
        if mode == 'hitting':
            stats = db.query(models.StandardBattingStat).filter(models.StandardBattingStat.player_id == player_id).order_by(models.StandardBattingStat.season.asc()).all()
        elif mode == 'pitching':
            stats = db.query(models.StandardPitchingStat).filter(models.StandardPitchingStat.player_id == player_id).order_by(models.StandardPitchingStat.season.asc()).all()
        else:
            return []
        overalls = []
        for stat in stats[-n_seasons:]:
            # For each season, extract features and calculate overall as in get_ratings
            feats = self.extract_player_features(db, player_id, mode=mode)
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
                command_rating = np.mean([norm[3], norm[4], norm[5], norm[20], norm[21], norm[22], norm[23], norm[7], norm[9]]) if len(norm) > 23 else 40.0
                tool_vals = [float(x) if x is not None else 40.0 for x in [k_rating, bb_rating, gb_rating, hr_rating, command_rating]]
                top_tools = sorted(tool_vals, reverse=True)[:3]
                overall = np.mean(top_tools)
            else:
                overall = 40.0
            overalls.append(self._scale_rating(float(overall), 40, 110))
        return overalls[-n_seasons:]

    def calculate_mlb_show_ratings(self, db: Session, player_id: int) -> Dict:
        player = db.query(models.Player).filter(models.Player.id == player_id).first()
        if not player:
            return {}
        ptype = self.get_player_type(player)
        def get_ratings(mode, pca_weights):
            # Define feature sets for confidence calculation
            def safe_float(val):
                try:
                    return float(val)
                except (TypeError, ValueError):
                    return 0.0
            hitting_feats = [
                safe_float(getattr(db.query(models.StandardBattingStat).filter(models.StandardBattingStat.player_id == player_id).order_by(models.StandardBattingStat.season.desc()).first(), 'ba', None)),
                safe_float(getattr(db.query(models.StandardBattingStat).filter(models.StandardBattingStat.player_id == player_id).order_by(models.StandardBattingStat.season.desc()).first(), 'obp', None)),
                safe_float(getattr(db.query(models.AdvancedBattingStat).filter(models.AdvancedBattingStat.player_id == player_id).order_by(models.AdvancedBattingStat.season.desc()).first(), 'ev', None)),
                safe_float(getattr(db.query(models.AdvancedBattingStat).filter(models.AdvancedBattingStat.player_id == player_id).order_by(models.AdvancedBattingStat.season.desc()).first(), 'hardh_pct', None)),
                safe_float(getattr(db.query(models.AdvancedBattingStat).filter(models.AdvancedBattingStat.player_id == player_id).order_by(models.AdvancedBattingStat.season.desc()).first(), 'ld_pct', None)),
                safe_float(getattr(db.query(models.StandardBattingStat).filter(models.StandardBattingStat.player_id == player_id).order_by(models.StandardBattingStat.season.desc()).first(), 'slg', None)),
                safe_float(getattr(db.query(models.AdvancedBattingStat).filter(models.AdvancedBattingStat.player_id == player_id).order_by(models.AdvancedBattingStat.season.desc()).first(), 'iso', None)),
                safe_float(getattr(db.query(models.AdvancedBattingStat).filter(models.AdvancedBattingStat.player_id == player_id).order_by(models.AdvancedBattingStat.season.desc()).first(), 'barrel_pct', None)),
                safe_float(getattr(db.query(models.StandardBattingStat).filter(models.StandardBattingStat.player_id == player_id).order_by(models.StandardBattingStat.season.desc()).first(), 'hr', None)),
                safe_float(getattr(db.query(models.AdvancedBattingStat).filter(models.AdvancedBattingStat.player_id == player_id).order_by(models.AdvancedBattingStat.season.desc()).first(), 'bb_pct', None)),
                safe_float(getattr(db.query(models.AdvancedBattingStat).filter(models.AdvancedBattingStat.player_id == player_id).order_by(models.AdvancedBattingStat.season.desc()).first(), 'so_pct', None)),
                safe_float(getattr(db.query(models.StandardBattingStat).filter(models.StandardBattingStat.player_id == player_id).order_by(models.StandardBattingStat.season.desc()).first(), 'bb', None)),
                safe_float(getattr(db.query(models.StandardBattingStat).filter(models.StandardBattingStat.player_id == player_id).order_by(models.StandardBattingStat.season.desc()).first(), 'so', None)),
                safe_float(getattr(db.query(models.StandardBattingStat).filter(models.StandardBattingStat.player_id == player_id).order_by(models.StandardBattingStat.season.desc()).first(), 'sb', None)),
                safe_float(getattr(db.query(models.ValueBattingStat).filter(models.ValueBattingStat.player_id == player_id).order_by(models.ValueBattingStat.season.desc()).first(), 'rbaser', None)),
            ]
            fielding_feats = [
                safe_float(getattr(db.query(models.StandardFieldingStat).filter(models.StandardFieldingStat.player_id == player_id).order_by(models.StandardFieldingStat.season.desc()).first(), 'fld_pct', None)),
                safe_float(getattr(db.query(models.StandardFieldingStat).filter(models.StandardFieldingStat.player_id == player_id).order_by(models.StandardFieldingStat.season.desc()).first(), 'rdrs', None)),
                safe_float(getattr(db.query(models.StandardFieldingStat).filter(models.StandardFieldingStat.player_id == player_id).order_by(models.StandardFieldingStat.season.desc()).first(), 'rtot', None)),
                safe_float(getattr(db.query(models.StandardFieldingStat).filter(models.StandardFieldingStat.player_id == player_id).order_by(models.StandardFieldingStat.season.desc()).first(), 'a', None)),
                safe_float(getattr(db.query(models.StandardFieldingStat).filter(models.StandardFieldingStat.player_id == player_id).order_by(models.StandardFieldingStat.season.desc()).first(), 'dp', None)),
            ]
            pitching_feats = [
                safe_float(getattr(db.query(models.AdvancedPitchingStat).filter(models.AdvancedPitchingStat.player_id == player_id).order_by(models.AdvancedPitchingStat.season.desc()).first(), 'k_pct', None)),
                safe_float(getattr(db.query(models.AdvancedPitchingStat).filter(models.AdvancedPitchingStat.player_id == player_id).order_by(models.AdvancedPitchingStat.season.desc()).first(), 'bb_pct', None)),
                safe_float(getattr(db.query(models.AdvancedPitchingStat).filter(models.AdvancedPitchingStat.player_id == player_id).order_by(models.AdvancedPitchingStat.season.desc()).first(), 'hr_pct', None)),
                safe_float(getattr(db.query(models.StandardPitchingStat).filter(models.StandardPitchingStat.player_id == player_id).order_by(models.StandardPitchingStat.season.desc()).first(), 'era', None)),
                safe_float(getattr(db.query(models.StandardPitchingStat).filter(models.StandardPitchingStat.player_id == player_id).order_by(models.StandardPitchingStat.season.desc()).first(), 'fip', None)),
                safe_float(getattr(db.query(models.StandardPitchingStat).filter(models.StandardPitchingStat.player_id == player_id).order_by(models.StandardPitchingStat.season.desc()).first(), 'whip', None)),
                safe_float(getattr(db.query(models.StandardPitchingStat).filter(models.StandardPitchingStat.player_id == player_id).order_by(models.StandardPitchingStat.season.desc()).first(), 'era_plus', None)),
                safe_float(getattr(db.query(models.ValuePitchingStat).filter(models.ValuePitchingStat.player_id == player_id).order_by(models.ValuePitchingStat.season.desc()).first(), 'war', None)),
                safe_float(getattr(db.query(models.ValuePitchingStat).filter(models.ValuePitchingStat.player_id == player_id).order_by(models.ValuePitchingStat.season.desc()).first(), 'waa', None)),
                safe_float(getattr(db.query(models.ValuePitchingStat).filter(models.ValuePitchingStat.player_id == player_id).order_by(models.ValuePitchingStat.season.desc()).first(), 'raa', None)),
                safe_float(getattr(db.query(models.StandardPitchingStat).filter(models.StandardPitchingStat.player_id == player_id).order_by(models.StandardPitchingStat.season.desc()).first(), 'so', None)),
                safe_float(getattr(db.query(models.StandardPitchingStat).filter(models.StandardPitchingStat.player_id == player_id).order_by(models.StandardPitchingStat.season.desc()).first(), 'bb', None)),
                safe_float(getattr(db.query(models.StandardPitchingStat).filter(models.StandardPitchingStat.player_id == player_id).order_by(models.StandardPitchingStat.season.desc()).first(), 'ip', None)),
                safe_float(getattr(db.query(models.StandardPitchingStat).filter(models.StandardPitchingStat.player_id == player_id).order_by(models.StandardPitchingStat.season.desc()).first(), 'gs', None)),
                safe_float(getattr(db.query(models.StandardPitchingStat).filter(models.StandardPitchingStat.player_id == player_id).order_by(models.StandardPitchingStat.season.desc()).first(), 'so9', None)),
                safe_float(getattr(db.query(models.StandardPitchingStat).filter(models.StandardPitchingStat.player_id == player_id).order_by(models.StandardPitchingStat.season.desc()).first(), 'bb9', None)),
                safe_float(getattr(db.query(models.StandardPitchingStat).filter(models.StandardPitchingStat.player_id == player_id).order_by(models.StandardPitchingStat.season.desc()).first(), 'hr9', None)),
                safe_float(getattr(db.query(models.StandardPitchingStat).filter(models.StandardPitchingStat.player_id == player_id).order_by(models.StandardPitchingStat.season.desc()).first(), 'h9', None)),
                safe_float(getattr(db.query(models.AdvancedPitchingStat).filter(models.AdvancedPitchingStat.player_id == player_id).order_by(models.AdvancedPitchingStat.season.desc()).first(), 'babip', None)),
                safe_float(getattr(db.query(models.AdvancedPitchingStat).filter(models.AdvancedPitchingStat.player_id == player_id).order_by(models.AdvancedPitchingStat.season.desc()).first(), 'lob_pct', None)),
                safe_float(getattr(db.query(models.AdvancedPitchingStat).filter(models.AdvancedPitchingStat.player_id == player_id).order_by(models.AdvancedPitchingStat.season.desc()).first(), 'era_minus', None)),
                safe_float(getattr(db.query(models.AdvancedPitchingStat).filter(models.AdvancedPitchingStat.player_id == player_id).order_by(models.AdvancedPitchingStat.season.desc()).first(), 'fip_minus', None)),
                safe_float(getattr(db.query(models.AdvancedPitchingStat).filter(models.AdvancedPitchingStat.player_id == player_id).order_by(models.AdvancedPitchingStat.season.desc()).first(), 'xfip_minus', None)),
                safe_float(getattr(db.query(models.AdvancedPitchingStat).filter(models.AdvancedPitchingStat.player_id == player_id).order_by(models.AdvancedPitchingStat.season.desc()).first(), 'siera', None)),
                safe_float(getattr(db.query(models.ValuePitchingStat).filter(models.ValuePitchingStat.player_id == player_id).order_by(models.ValuePitchingStat.season.desc()).first(), 'wpa', None)),
                safe_float(getattr(db.query(models.ValuePitchingStat).filter(models.ValuePitchingStat.player_id == player_id).order_by(models.ValuePitchingStat.season.desc()).first(), 're24', None)),
                safe_float(getattr(db.query(models.ValuePitchingStat).filter(models.ValuePitchingStat.player_id == player_id).order_by(models.ValuePitchingStat.season.desc()).first(), 'cwpa', None)),
            ]
            feats = self.extract_player_features(db, int(player_id), mode=mode)
            if feats is None:
                return {}
            norm = feats["normalized"]
            def pca_tool(indices):
                vals = [float(norm[i]) for i in indices if norm[i] is not None]
                if not vals:
                    return 40.0
                if pca_weights is not None:
                    return float(np.dot(np.array(vals), np.array([pca_weights[i] for i in indices if norm[i] is not None])))
                return float(np.mean(vals))
            contact = pca_tool([0,1,2,3,4])
            power = pca_tool([5,6,7,8])
            discipline = pca_tool([9,10,11,12])
            vision = pca_tool([9,10,0])
            fielding = pca_tool([15,16,17]) if len(norm) > 17 else 40.0
            arm_strength = pca_tool([18,19]) if len(norm) > 19 else 40.0
            arm_accuracy = pca_tool([18,15]) if len(norm) > 18 else 40.0
            speed = pca_tool([13,14]) if len(norm) > 14 else 40.0
            stealing = pca_tool([13,14]) if len(norm) > 14 else 40.0
            k_rating = pca_tool([0, 10, 14]) if mode == 'pitching' else None
            bb_rating = 100 - pca_tool([1, 11, 15]) if mode == 'pitching' else None
            gb_rating = pca_tool([19, 23]) if mode == 'pitching' else None
            hr_rating = 100 - pca_tool([2, 16]) if mode == 'pitching' else None
            command_rating = pca_tool([3,4,5,20,21,22,23,7,9]) if mode == 'pitching' else None
            durability_rating = pca_tool([12,13,7]) if mode == 'pitching' else None
            leverage_rating = pca_tool([24,25,26]) if mode == 'pitching' else None
            ratings = {}
            if mode == 'hitting':
                tool_vals = [float(x) if x is not None else 40.0 for x in [contact, power, discipline, vision, fielding, arm_strength, arm_accuracy, speed, stealing]]
                top_tools = sorted(tool_vals, reverse=True)[:4]
                overall = np.mean(top_tools)
                feats_raw = feats['raw'][:len(hitting_feats) + len(fielding_feats)]
                n_present = np.count_nonzero([x not in (None, 0.0) for x in feats_raw])
                confidence = n_present / len(feats_raw) if len(feats_raw) > 0 else 0.0
                potential = self._calculate_trend_potential(
                    self._get_recent_overalls(db, player_id, 'hitting'),
                    self._scale_rating(float(overall), 40, 110),
                    db=db, player_id=player_id, mode='hitting'
                )
                ratings = {
                    'contact_left': self._scale_rating(float(contact), 40, 110),
                    'contact_right': self._scale_rating(float(contact), 40, 110),
                    'power_left': self._scale_rating(float(power), 40, 120),
                    'power_right': self._scale_rating(float(power), 40, 120),
                    'discipline': self._scale_rating(float(discipline), 20, 100),
                    'vision': self._scale_rating(float(vision), 20, 100),
                    'fielding': self._scale_rating(float(fielding), 40, 100),
                    'arm_strength': self._scale_rating(float(arm_strength), 40, 100),
                    'arm_accuracy': self._scale_rating(float(arm_accuracy), 40, 100),
                    'speed': self._scale_rating(float(speed), 40, 100),
                    'stealing': self._scale_rating(float(stealing), 40, 100),
                    'overall_rating': self._scale_rating(float(overall), 40, 110),
                    'potential_rating': potential,
                    'confidence_score': confidence,
                    'player_type': 'position_player',
                }
            elif mode == 'pitching':
                tool_vals = [float(x) if x is not None else 40.0 for x in [k_rating, bb_rating, gb_rating, hr_rating, command_rating]]
                top_tools = sorted(tool_vals, reverse=True)[:3]
                overall = np.mean(top_tools)
                offset = len(hitting_feats) + len(fielding_feats)
                feats_raw = feats['raw'][offset:offset+len(pitching_feats)]
                n_present = np.count_nonzero([x not in (None, 0.0) for x in feats_raw])
                confidence = n_present / len(feats_raw) if len(feats_raw) > 0 else 0.0
                potential = self._calculate_trend_potential(
                    self._get_recent_overalls(db, player_id, 'pitching'),
                    self._scale_rating(float(overall), 40, 110),
                    db=db, player_id=player_id, mode='pitching'
                )
                ratings = {
                    'k_rating': self._scale_rating(float(k_rating) if k_rating is not None else 40.0, 40, 110),
                    'bb_rating': self._scale_rating(float(bb_rating) if bb_rating is not None else 40.0, 40, 110),
                    'gb_rating': self._scale_rating(float(gb_rating) if gb_rating is not None else 40.0, 40, 110),
                    'hr_rating': self._scale_rating(float(hr_rating) if hr_rating is not None else 40.0, 40, 110),
                    'command_rating': self._scale_rating(float(command_rating) if command_rating is not None else 40.0, 40, 110),
                    'durability_rating': self._scale_rating(float(durability_rating) if durability_rating is not None else 40.0, 40, 110),
                    'leverage_rating': self._scale_rating(float(leverage_rating) if leverage_rating is not None else 40.0, 40, 110),
                    'overall_rating': self._scale_rating(float(overall), 40, 110),
                    'potential_rating': potential,
                    'confidence_score': confidence,
                    'player_type': 'pitcher',
                }
            return ratings
        if ptype == 'pitcher':
            return get_ratings('pitching', getattr(self, 'pca_weights_pit', None))
        elif ptype in ('position_player', 'dh'):
            return get_ratings('hitting', getattr(self, 'pca_weights_hit', None))
        elif ptype == 'two_way':
            hit = get_ratings('hitting', getattr(self, 'pca_weights_hit', None))
            pit = get_ratings('pitching', getattr(self, 'pca_weights_pit', None))
            batting_potential = hit.get('potential_rating', 0)
            pitching_potential = pit.get('potential_rating', 0)
            overall = 0.6 * max(hit.get('overall_rating', 0), pit.get('overall_rating', 0)) + 0.4 * min(hit.get('overall_rating', 0), pit.get('overall_rating', 0))
            potential = 0.6 * max(batting_potential, pitching_potential) + 0.4 * min(batting_potential, pitching_potential)
            return {
                'hitting': hit,
                'pitching': pit,
                'player_type': 'two_way',
                'overall_rating': overall,
                'potential_rating': potential
            }
        else:
            return {}
    
    def _scale_rating(self, value: float, min_val: float, max_val: float) -> float:
        """Scale a stat from 0-100 normalized value to the desired scout rating range (e.g., 40-99), capped at 99."""
        # Clamp value to 0-100
        value = np.clip(value, 0, 100)
        # Map 0 -> min_val, 100 -> max_val, then cap at 99
        scaled = min(float(np.round(min_val + (value / 100.0) * (max_val - min_val), 1)), 99.0)
        return scaled
    
    def auto_fit_if_needed(self, db: Session):
        # Auto-retrain if number of players or stats has changed
        n_players = db.query(models.Player).count()
        n_stats = db.query(models.StandardBattingStat).count() + db.query(models.StandardPitchingStat).count()
        if not self.is_fitted or n_players != self.last_n_players or n_stats != self.last_n_stats:
            logger.info("Auto-fitting models due to data change or first use.")
            self.fit_models(db)
    
    def _check_and_fix_feature_dimensions(self, db: Session, features: np.ndarray) -> bool:
        """Check if feature dimensions match the trained model and retrain if needed"""
        try:
            # Check if model is fitted and has expected dimensions
            if hasattr(self, 'expected_feature_count') and hasattr(self.overall_rating_model, 'estimators_'):
                # Try to predict with a dummy sample to check dimensions
                try:
                    _ = self.overall_rating_model.predict([features.flatten()])
                    return False  # No dimension mismatch
                except ValueError as e:
                    if "features" in str(e).lower():
                        logger.warning(f"Feature dimension mismatch detected. Retraining model.")
                        self.fit_models(db)
                        return True
            return False
        except Exception as e:
            logger.error(f"Error checking feature dimensions: {e}")
            return False

    def predict_mlb_success(self, db: Session, player_id: int) -> dict:
        self.auto_fit_if_needed(db)
        feats = self.extract_player_features(db, int(player_id))
        if feats is None:
            return {}
        features = feats["normalized"]
        raw_features = feats["raw"]
        level_factor = feats["level_factor"] * 100  # for consistency with previous logic
        age_factor = features[10]
        player = db.query(models.Player).filter(models.Player.id == player_id).first()
        ptype = self.get_player_type(player)
        def safe_float(val):
            try:
                return float(val)
            except (TypeError, ValueError):
                return 0.0
        # --- Career WAR calculation ---
        current_career_war = 0.0
        if ptype == 'pitcher':
            # Sum WAR from all ValuePitchingStat rows
            war_vals = [safe_float(s.war) for s in db.query(models.ValuePitchingStat).filter(models.ValuePitchingStat.player_id == player_id).all() if s.war is not None]
            current_career_war = float(np.nansum(war_vals)) if war_vals else 0.0
        elif ptype in ('position_player', 'dh'):
            # Sum oWAR + dWAR from all ValueBattingStat rows
            owar_vals = [safe_float(s.owar) for s in db.query(models.ValueBattingStat).filter(models.ValueBattingStat.player_id == player_id).all() if s.owar is not None]
            dwar_vals = [safe_float(s.dwar) for s in db.query(models.ValueBattingStat).filter(models.ValueBattingStat.player_id == player_id).all() if s.dwar is not None]
            current_career_war = float(np.nansum(owar_vals) + np.nansum(dwar_vals)) if (owar_vals or dwar_vals) else 0.0
        elif ptype == 'two_way':
            # Sum both
            owar_vals = [safe_float(s.owar) for s in db.query(models.ValueBattingStat).filter(models.ValueBattingStat.player_id == player_id).all() if s.owar is not None]
            dwar_vals = [safe_float(s.dwar) for s in db.query(models.ValueBattingStat).filter(models.ValueBattingStat.player_id == player_id).all() if s.dwar is not None]
            war_vals = [safe_float(s.war) for s in db.query(models.ValuePitchingStat).filter(models.ValuePitchingStat.player_id == player_id).all() if s.war is not None]
            current_career_war = float(np.nansum(owar_vals) + np.nansum(dwar_vals) + np.nansum(war_vals)) if (owar_vals or dwar_vals or war_vals) else 0.0
        # --- MLBer logic ---
        is_mlber = (feats["level"] == "MLB" or current_career_war > 0)
        hall_of_fame_probability = None
        debut_year = None
        if is_mlber:
            # Hall of Fame probability based on career WAR
            if current_career_war >= 60:
                hall_of_fame_probability = 0.95
            elif current_career_war >= 40:
                hall_of_fame_probability = 0.5
            elif current_career_war >= 20:
                hall_of_fame_probability = 0.1
            else:
                hall_of_fame_probability = 0.01
            # Debut year from debut_date if present, else infer from stats
            debut_date = getattr(player, 'debut_date', None)
            if debut_date:
                try:
                    debut_year = int(str(debut_date)[:4])
                except Exception:
                    debut_year = None
            if not debut_year:
                # Try to infer from earliest stat season
                bat_season = db.query(models.StandardBattingStat).filter(models.StandardBattingStat.player_id == player_id).order_by(models.StandardBattingStat.season.asc()).first()
                pit_season = db.query(models.StandardPitchingStat).filter(models.StandardPitchingStat.player_id == player_id).order_by(models.StandardPitchingStat.season.asc()).first()
                seasons = []
                if bat_season and getattr(bat_season, 'season', None):
                    try:
                        seasons.append(int(str(bat_season.season)[:4]))
                    except Exception:
                        pass
                if pit_season and getattr(pit_season, 'season', None):
                    try:
                        seasons.append(int(str(pit_season.season)[:4]))
                    except Exception:
                        pass
                if seasons:
                    debut_year = min(seasons)
            # Projected career WAR = current + nuanced future projection for active players
            # Try to estimate age from birth_date
            birth_date = getattr(player, 'birth_date', None)
            age = None
            if birth_date:
                try:
                    birth_year = int(str(birth_date)[:4])
                    from datetime import datetime
                    age = datetime.now().year - birth_year
                except Exception:
                    pass
            # Compute recent WAR (average of last 3 seasons)
            recent_wars = []
            for stat_model in [models.ValueBattingStat, models.ValuePitchingStat]:
                stats = db.query(stat_model).filter(stat_model.player_id == player_id).order_by(stat_model.season.desc()).limit(3).all()
                for s in stats:
                    war_val = safe_float(getattr(s, 'war', None))
                    if war_val:
                        recent_wars.append(war_val)
            recent_war = np.mean(recent_wars) if recent_wars else None
            projected_remaining_years = 0
            projected_avg_war_per_year = 0.0
            future_war = 0.0
            if age is not None and recent_war is not None:
                if age < 32:
                    projected_remaining_years = 5
                    projected_avg_war_per_year = recent_war
                    future_war = 3 * recent_war + 2 * (recent_war * 0.7)
                elif age < 35:
                    projected_remaining_years = 4
                    projected_avg_war_per_year = recent_war
                    future_war = 2 * recent_war + 2 * (recent_war * 0.6)
                elif age < 38:
                    projected_remaining_years = 2
                    projected_avg_war_per_year = recent_war
                    future_war = 1 * recent_war + 1 * (recent_war * 0.5)
                else:
                    projected_remaining_years = 1
                    projected_avg_war_per_year = recent_war * 0.3
                    future_war = 1 * (recent_war * 0.3)
            else:
                # Fallback if no recent WAR or age
                future_war = 2.0
                projected_remaining_years = 1
                projected_avg_war_per_year = 2.0
            projected_war = current_career_war + future_war
            # Ceiling/floor based on career WAR
            if current_career_war >= 60:
                ceiling = "Hall of Fame"
                floor = "All-Star"
            elif current_career_war >= 40:
                ceiling = "All-Star"
                floor = "Above-average regular"
            elif current_career_war >= 20:
                ceiling = "Above-average regular"
                floor = "MLB regular"
            else:
                ceiling = "MLB regular"
                floor = "Bench/role player"
        else:
            # Use ML model if fitted
            model_fitted = False
            try:
                # Check if model is fitted by accessing estimators_
                _ = self.overall_rating_model.estimators_
                model_fitted = True
            except AttributeError:
                model_fitted = False
            
            # Check feature dimensions and retrain if needed
            self._check_and_fix_feature_dimensions(db, features.reshape(1, -1))
            
            if self.is_fitted and model_fitted:
                try:
                    overall_quality = float(self.overall_rating_model.predict([features])[0])
                    # Use correct X_scaled for player type
                    if ptype == 'pitcher' and hasattr(self, 'Xp_scaled'):
                        all_ratings = self.overall_rating_model.predict(self.Xp_scaled)
                        pct = (all_ratings < overall_quality).sum() / len(all_ratings)
                    elif ptype in ('position_player', 'dh') and hasattr(self, 'Xh_scaled'):
                        all_ratings = self.overall_rating_model.predict(self.Xh_scaled)
                        pct = (all_ratings < overall_quality).sum() / len(all_ratings)
                    else:
                        pct = 0.5
                except ValueError as e:
                    # If there's still a dimension mismatch, fall back to basic calculation
                    logger.warning(f"Model prediction failed due to dimension mismatch: {e}")
                    overall_quality = float(np.mean(features[:10]))
                    pct = 0.5
            else:
                overall_quality = float(np.mean(features[:10]))
                pct = 0.5
            pca_score = self._pca_composite_score(features)
            projected_war = float(np.clip((overall_quality - 40) / 6, 0, 10))
            mlb_debut_prob_model = float(1 / (1 + np.exp(-0.1 * (overall_quality - 60))))
            mlb_debut_prob_model = round(mlb_debut_prob_model, 2)
            if level_factor >= 100:
                mlb_debut_prob = 1.0
            else:
                mlb_debut_prob = mlb_debut_prob_model
            if overall_quality > 80 or level_factor > 80:
                eta = 2025
            elif overall_quality > 65 or level_factor > 60:
                eta = 2026
            else:
                eta = 2027
            if age_factor < 70 or level_factor < 50:
                risk = "High"
            elif age_factor < 80 or level_factor < 70:
                risk = "Medium"
            else:
                risk = "Low"
            # More realistic ceiling/floor logic
            if mlb_debut_prob < 0.8 or overall_quality < 60:
                ceiling = "Bench/role player"
            elif pct > 0.98 and mlb_debut_prob > 0.95 and overall_quality > 90:
                ceiling = "Hall of Fame caliber"
            elif pct > 0.90 and mlb_debut_prob > 0.90 and overall_quality > 80:
                ceiling = "All-Star caliber"
            elif pct > 0.75 and mlb_debut_prob > 0.85 and overall_quality > 70:
                ceiling = "Above-average regular"
            elif pct > 0.5 and mlb_debut_prob > 0.7 and overall_quality > 60:
                ceiling = "Average regular"
            else:
                ceiling = "Bench/role player"
            if mlb_debut_prob < 0.5 or overall_quality < 50:
                floor = "Minor league depth"
            elif pct > 0.7 and mlb_debut_prob > 0.8 and overall_quality > 60:
                floor = "MLB regular"
            elif pct > 0.5 and mlb_debut_prob > 0.6 and overall_quality > 55:
                floor = "MLB bench player"
            else:
                floor = "Minor league depth"
            debut_year = None
            hall_of_fame_probability = None
        # Compose response
        return {
            'mlb_debut_probability': 1.0 if is_mlber else mlb_debut_prob,
            'mlb_debut_probability_model': None if is_mlber else mlb_debut_prob_model if 'mlb_debut_prob_model' in locals() else None,
            'projected_career_war': projected_war,
            'current_career_war': current_career_war,
            'projected_remaining_years': projected_remaining_years if is_mlber else None,
            'projected_avg_war_per_year': projected_avg_war_per_year if is_mlber else None,
            'risk_factor': risk if not is_mlber else None,
            'eta_mlb': debut_year if is_mlber and debut_year else eta if not is_mlber else None,
            'debut_date': getattr(player, 'debut_date', None) if is_mlber else None,
            'ceiling_comparison': ceiling,
            'floor_comparison': floor,
            'hall_of_fame_probability': hall_of_fame_probability,
            'debug_features': raw_features.tolist(),
            'debug_normalized_features': features.tolist(),
            'pca_composite_score': self._pca_composite_score(features),
            'ml_model_overall_rating': None if is_mlber else overall_quality if 'overall_quality' in locals() else None,
            'level': feats["level"],
            'level_factor': feats["level_factor"],
        }

    def debug_player_ratings(self, db: Session, player_names: list):
        """Print raw, normalized, and scaled ratings for a list of player names."""
        for name in player_names:
            player = db.query(models.Player).filter(models.Player.full_name.ilike(f"%{name}%")).first()
            if not player:
                print(f"[DEBUG] Player not found: {name}")
                continue
            player_id = getattr(player, 'id', None)
            if player_id is None:
                continue
            feats = self.extract_player_features(db, int(player_id))
            if feats is None:
                print(f"[DEBUG] No features for {name}")
                continue
            print(f"\n[DEBUG] Player: {player.full_name} (Type: {self.get_player_type(player)})")
            print("Raw features:", feats['raw'])
            print("Normalized features:", feats['normalized'])
            ratings = self.calculate_mlb_show_ratings(db, int(player_id))
            print("Ratings:", ratings)

# Global instance
ml_service = BaseballMLService()

# --- Debug script for player feature/rating inspection ---
if __name__ == "__main__":
    from backend.database import SessionLocal
    db = SessionLocal()
    sample_names = ["Ohtani", "Arenado", "Sale", "Judge", "Cole", "Velasquez"]
    for name in sample_names:
        player = db.query(models.Player).filter(models.Player.full_name.ilike(f"%{name}%")).first()
        if not player:
            print(f"[DEBUG] Player not found: {name}")
            continue
        player_id = getattr(player, 'id', None)
        if player_id is None:
            continue
        feats = ml_service.extract_player_features(db, int(player_id))
        if feats is None:
            print(f"[DEBUG] No features for {name}")
            continue
        ratings = ml_service.calculate_mlb_show_ratings(db, int(player_id))
        print(f"\n[DEBUG] Player: {player.full_name} (Type: {ml_service.get_player_type(player)})")
        print("Raw features:", feats['raw'])
        print("Normalized features:", feats['normalized'])
        print("Ratings:", ratings)
    db.close() 