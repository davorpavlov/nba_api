"""
Helper funkcije za NBA analizu
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_logger(name: str, log_file: Optional[str] = None, level=logging.INFO):
    """Setup custom logger"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


def calculate_average(df: pd.DataFrame, column: str, last_n: Optional[int] = None) -> float:
    """Izračunaj prosjek za kolonu"""
    if df.empty:
        return 0.0

    data = df[column] if last_n is None else df[column].head(last_n)
    return float(data.mean()) if not data.empty else 0.0


def calculate_consistency(df: pd.DataFrame, column: str, threshold: float, last_n: Optional[int] = None) -> float:
    """
    Izračunaj konzistentnost (% utakmica iznad threshold-a)

    Args:
        df: DataFrame sa podacima
        column: Kolona za analizu
        threshold: Prag vrijednosti
        last_n: Broj zadnjih utakmica

    Returns:
        Procenat utakmica gdje je stat >= threshold
    """
    if df.empty:
        return 0.0

    data = df[column] if last_n is None else df[column].head(last_n)
    if data.empty:
        return 0.0

    above_threshold = (data >= threshold).sum()
    return float(above_threshold / len(data))


def calculate_trend(df: pd.DataFrame, column: str, last_n: int = 5) -> str:
    """
    Odredi trend (up, down, stable)

    Args:
        df: DataFrame sa podacima
        column: Kolona za analizu
        last_n: Broj utakmica za trend

    Returns:
        'up', 'down', ili 'stable'
    """
    if df.empty or len(df) < last_n:
        return 'stable'

    recent = df[column].head(last_n).mean()
    older = df[column].iloc[last_n:last_n*2].mean() if len(df) >= last_n*2 else recent

    if older == 0:
        return 'stable'

    change = (recent - older) / older

    if change > 0.10:  # 10%+ porast
        return 'up'
    elif change < -0.10:  # 10%+ pad
        return 'down'
    else:
        return 'stable'


def calculate_std_deviation(df: pd.DataFrame, column: str, last_n: Optional[int] = None) -> float:
    """Izračunaj standardnu devijaciju"""
    if df.empty:
        return 0.0

    data = df[column] if last_n is None else df[column].head(last_n)
    return float(data.std()) if not data.empty else 0.0


def get_home_away_split(df: pd.DataFrame, column: str, is_home: bool) -> Dict:
    """
    Izračunaj home/away split statistike

    Args:
        df: DataFrame sa game log podacima (mora imati 'MATCHUP' kolonu)
        column: Stat kolona
        is_home: True za home, False za away

    Returns:
        Dict sa avg, games, consistency
    """
    if df.empty or 'MATCHUP' not in df.columns:
        return {'avg': 0.0, 'games': 0, 'std': 0.0}

    # Home games imaju 'vs.' u MATCHUP koloni
    home_games = df[df['MATCHUP'].str.contains('vs.', na=False)]
    away_games = df[df['MATCHUP'].str.contains('@', na=False)]

    games_df = home_games if is_home else away_games

    if games_df.empty:
        return {'avg': 0.0, 'games': 0, 'std': 0.0}

    return {
        'avg': float(games_df[column].mean()),
        'games': len(games_df),
        'std': float(games_df[column].std())
    }


def normalize_score(value: float, min_val: float, max_val: float) -> float:
    """
    Normaliziraj vrijednost na scale 0-1

    Args:
        value: Vrijednost za normalizaciju
        min_val: Minimalna vrijednost
        max_val: Maksimalna vrijednost

    Returns:
        Normalizirana vrijednost između 0 i 1
    """
    if max_val == min_val:
        return 0.5

    normalized = (value - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, normalized))  # Clamp između 0 i 1


def get_confidence_label(score: float) -> str:
    """
    Odredi confidence label na osnovu score-a

    Args:
        score: Confidence score (0-1)

    Returns:
        Label: 'very_high', 'high', 'medium', 'low', 'very_low'
    """
    if score >= 0.80:
        return 'very_high'
    elif score >= 0.70:
        return 'high'
    elif score >= 0.60:
        return 'medium'
    elif score >= 0.50:
        return 'low'
    else:
        return 'very_low'


def get_recommendation(score: float, prop_line: float, projected: float) -> str:
    """
    Generiši preporuku na osnovu score-a i projekcije

    Args:
        score: Confidence score
        prop_line: Betting linija
        projected: Projektivna vrijednost

    Returns:
        'STRONG OVER', 'OVER', 'LEAN OVER', 'PASS', 'LEAN UNDER', 'UNDER', 'STRONG UNDER'
    """
    diff = projected - prop_line
    diff_pct = abs(diff / prop_line) if prop_line > 0 else 0

    # OVER scenarios
    if diff > 0:
        if score >= 0.75 and diff_pct >= 0.15:  # 75%+ confidence, 15%+ edge
            return 'STRONG OVER'
        elif score >= 0.65 and diff_pct >= 0.10:  # 65%+ confidence, 10%+ edge
            return 'OVER'
        elif score >= 0.55:
            return 'LEAN OVER'

    # UNDER scenarios
    elif diff < 0:
        if score >= 0.75 and diff_pct >= 0.15:
            return 'STRONG UNDER'
        elif score >= 0.65 and diff_pct >= 0.10:
            return 'UNDER'
        elif score >= 0.55:
            return 'LEAN UNDER'

    return 'PASS'


def format_output(results: List[Dict], format_type: str = 'table') -> str:
    """
    Formatiraj output za prikaz

    Args:
        results: Lista rezultata
        format_type: 'table', 'json', 'simple'

    Returns:
        Formatiran string
    """
    if not results:
        return "Nema rezultata"

    if format_type == 'json':
        import json
        return json.dumps(results, indent=2)

    elif format_type == 'table':
        df = pd.DataFrame(results)
        return df.to_string(index=False)

    else:  # simple
        output = []
        for r in results:
            output.append(
                f"{r.get('player_name', 'Unknown')} - {r.get('prop_type', 'N/A')}: "
                f"{r.get('recommendation', 'PASS')} "
                f"(Confidence: {r.get('confidence_score', 0):.1%})"
            )
        return '\n'.join(output)


def safe_api_call(func, *args, max_retries: int = 3, **kwargs):
    """
    Safely pozovi API sa retry logikom

    Args:
        func: Funkcija za poziv
        max_retries: Maksimalan broj pokušaja
        *args, **kwargs: Argumenti za funkciju

    Returns:
        Rezultat funkcije ili None
    """
    import time

    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"API call failed after {max_retries} attempts")
                return None


def parse_game_date(date_str: str) -> datetime:
    """Parse game date string to datetime"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        try:
            return datetime.strptime(date_str, '%b %d, %Y')
        except:
            return datetime.now()


def is_recent_game(game_date: str, days: int = 30) -> bool:
    """Provjeri da li je utakmica skorija od N dana"""
    try:
        game_dt = parse_game_date(game_date)
        return (datetime.now() - game_dt).days <= days
    except:
        return False
