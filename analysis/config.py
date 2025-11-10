"""
Konfiguracija za NBA analizu
"""

# API Configuration
API_TIMEOUT = 30  # sekundi
CACHE_ENABLED = True
CACHE_DURATION = 3600  # 1 sat

# Analysis Configuration
CURRENT_SEASON = "2025-26"
DEFAULT_GAMES_SAMPLE = 10  # Broj utakmica za analizu forme

# Scoring Weights (ukupno = 1.0)
SCORING_WEIGHTS = {
    'recent_form': 0.25,          # 25% - Forma u zadnjih N utakmica
    'opponent_matchup': 0.20,     # 20% - Historijski vs opponent
    'home_away_split': 0.15,      # 15% - Home/Away performance
    'opponent_defense': 0.20,     # 20% - Opponent defensive stats
    'pace_factor': 0.10,          # 10% - Tempo utakmice
    'usage_factor': 0.10,         # 10% - Usage rate (injuries impact)
}

# Props Types
PROPS_TYPES = {
    'points': {
        'stat_column': 'PTS',
        'min_games': 5,
        'consistency_threshold': 0.7
    },
    'rebounds': {
        'stat_column': 'REB',
        'min_games': 5,
        'consistency_threshold': 0.7
    },
    'assists': {
        'stat_column': 'AST',
        'min_games': 5,
        'consistency_threshold': 0.6
    },
    'threes': {
        'stat_column': 'FG3M',
        'min_games': 5,
        'consistency_threshold': 0.5
    },
    'pts_reb_ast': {
        'stat_columns': ['PTS', 'REB', 'AST'],
        'min_games': 5,
        'consistency_threshold': 0.7
    }
}

# Confidence Levels
CONFIDENCE_LEVELS = {
    'very_high': 0.80,   # 80%+ confidence
    'high': 0.70,        # 70-80% confidence
    'medium': 0.60,      # 60-70% confidence
    'low': 0.50,         # 50-60% confidence
    'very_low': 0.0      # < 50% confidence
}

# Output Configuration
OUTPUT_FORMAT = 'json'  # 'json', 'csv', 'excel'
OUTPUT_DIR = './output'

# Logging
LOG_LEVEL = 'INFO'  # 'DEBUG', 'INFO', 'WARNING', 'ERROR'
LOG_FILE = './logs/nba_analysis.log'
