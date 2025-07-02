# backend/ml/ratings_config.py

# Tool weights for hitters (can be tuned per position later)
HITTER_TOOL_WEIGHTS = {
    'contact': 0.25,
    'power': 0.25,
    'discipline': 0.15,
    'vision': 0.10,
    'speed': 0.10,
    'fielding': 0.10,
    'arm_strength': 0.05,
}

# Stat mapping for each tool (stat: weight)
HITTER_TOOL_STATS = {
    'contact': {'ba': 0.6, 'k_pct': 0.2, 'obp': 0.2},
    'power': {'hr': 0.5, 'iso': 0.3, 'slg': 0.2},
    'discipline': {'bb_pct': 0.6, 'obp': 0.4},
    'vision': {'k_pct': 1.0},  # Inverted
    'speed': {'sb': 0.6, 'sprint_speed': 0.4},
    'fielding': {'drs': 0.5, 'fld_pct': 0.5},
    'arm_strength': {'of_assists': 0.6, 'max_throw': 0.4},
    'arm_accuracy': {'errors': 0.7, 'fld_pct': 0.3},  # Inverted errors
    'stealing': {'sb': 1.0},
}

# Min/max for normalization (stat: (min, max)). Invert where lower is better.
HITTER_TOOL_MIN_MAX = {
    'ba': (0.220, 0.320),
    'k_pct': (30, 10),  # Inverted
    'obp': (0.280, 0.420),
    'hr': (0, 40),
    'iso': (0.100, 0.250),
    'slg': (0.350, 0.600),
    'bb_pct': (3, 15),
    'sb': (0, 40),
    'sprint_speed': (23, 30),  # ft/sec, Statcast
    'drs': (-10, 20),
    'fld_pct': (0.950, 1.000),
    'of_assists': (0, 15),
    'max_throw': (75, 105),  # mph
    'errors': (30, 0),  # Inverted
} 