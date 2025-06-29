import math

def stat_to_grade(stat, min_val, max_val):
    if stat is None or min_val == max_val:
        return 20
    pct = (stat - min_val) / (max_val - min_val)
    pct = max(0, min(1, pct))
    return int(20 + pct * 60)

# Example config for stat mappings and min/max by level/position
STAT_CONFIG = {
    'default': {
        'hit':    {'stats': ['batting_avg', 'obp'], 'min': 0.15, 'max': 0.45},
        'power':  {'stats': ['home_runs', 'slugging_pct', 'iso'], 'min': 0, 'max': 50},
        'run':    {'stats': ['stolen_bases', 'triples'], 'min': 0, 'max': 40},
        'arm':    {'stats': ['outfield_assists', 'caught_stealing'], 'min': 0, 'max': 20},
        'field':  {'stats': ['fielding_pct'], 'min': 0.85, 'max': 1.0},
    },
    'C': {  # Catcher
        'arm': {'stats': ['caught_stealing'], 'min': 0, 'max': 20},
        'field': {'stats': ['fielding_pct'], 'min': 0.85, 'max': 1.0},
    },
    'SS': {  # Shortstop
        'arm': {'stats': ['outfield_assists'], 'min': 0, 'max': 20},
        'field': {'stats': ['fielding_pct'], 'min': 0.85, 'max': 1.0},
    },
    'OF': {  # Outfield
        'arm': {'stats': ['outfield_assists'], 'min': 0, 'max': 20},
    },
    # Add more positions as needed
}

LEVEL_ADJUST = {
    'HS': 0.9,
    'NCAA': 1.0,
    'MiLB': 1.1,
    'MLB': 1.2,
}

TOOLS = ['hit', 'power', 'run', 'arm', 'field']

def get_stat(stats, keys):
    for k in keys:
        if k in stats and stats[k] is not None:
            return stats[k]
    return None

def generate_player_grades(player):
    if isinstance(player, dict):
        stats = player.get('stats_json', {})
        level = player.get('level', '')
        position = player.get('position', '')
    else:
        stats = getattr(player, 'stats_json', {})
        level = getattr(player, 'level', '')
        position = getattr(player, 'position', '')
    level = (level or '').upper()
    position = (position or '').upper()
    config = STAT_CONFIG.get(position, STAT_CONFIG['default'])
    level_factor = LEVEL_ADJUST.get(level, 1.0)
    grades = {}
    for tool in TOOLS:
        try:
            tool_cfg = config.get(tool)
            if not tool_cfg:
                tool_cfg = STAT_CONFIG['default'].get(tool)
            if not tool_cfg:
                print(f"[WARN] No config found for tool '{tool}' in position '{position}'. Defaulting to 20.")
                grades[tool] = 20
                continue
            stat_val = get_stat(stats, tool_cfg['stats'])
            grades[tool] = stat_to_grade(stat_val, tool_cfg['min'], tool_cfg['max'])
        except Exception as e:
            print(f"[ERROR] Exception grading tool '{tool}' for player {getattr(player, 'id', None)}: {e}")
            grades[tool] = 20
    # Apply level adjustment (slightly boost grades for higher levels)
    for k in grades:
        grades[k] = int(min(80, max(20, math.ceil(grades[k] * level_factor))))
    grades['overall'] = int(sum(grades.values()) / len(grades))
    return grades 