"""
Scoring Model za NBA Props analizu
Kombinuje različite faktore u jedinstveni confidence score
"""

import logging
from typing import Dict, Optional, List, Tuple
import pandas as pd
import numpy as np

from .wrappers import NBADataFetcher
from .config import SCORING_WEIGHTS, PROPS_TYPES, DEFAULT_GAMES_SAMPLE
from .utils import (
    calculate_average,
    calculate_consistency,
    calculate_trend,
    calculate_std_deviation,
    get_home_away_split,
    normalize_score,
    get_confidence_label,
    get_recommendation,
    logger
)

logger = logging.getLogger(__name__)


class PropsScoringModel:
    """
    Model za analizu player props sa confidence scoring-om
    """

    def __init__(self, data_fetcher: NBADataFetcher):
        """
        Args:
            data_fetcher: NBADataFetcher instanca
        """
        self.fetcher = data_fetcher
        self.weights = SCORING_WEIGHTS
        logger.info("PropsScoringModel initialized")

    def analyze_player_prop(
        self,
        player_id: int,
        player_name: str,
        team_id: int,
        opponent_team_id: int,
        prop_type: str,
        prop_line: float,
        is_home_game: bool,
        last_n_games: int = DEFAULT_GAMES_SAMPLE
    ) -> Dict:
        """
        Glavna metoda za analizu player prop-a

        Args:
            player_id: NBA player ID
            player_name: Ime igrača
            team_id: Team ID
            opponent_team_id: Opponent team ID
            prop_type: Tip prop-a ('points', 'rebounds', 'assists', etc.)
            prop_line: Betting linija
            is_home_game: Da li je home utakmica
            last_n_games: Broj utakmica za analizu forme

        Returns:
            Dict sa kompletnom analizom i confidence score-om
        """
        logger.info(f"Analyzing {prop_type} prop for {player_name} (line: {prop_line})")

        # Validiraj prop type
        if prop_type not in PROPS_TYPES:
            logger.error(f"Invalid prop type: {prop_type}")
            return self._empty_result(player_name, prop_type, prop_line, "Invalid prop type")

        prop_config = PROPS_TYPES[prop_type]
        stat_column = prop_config['stat_column']

        # Dohvati sve potrebne podatke
        data = self._fetch_all_data(
            player_id, team_id, opponent_team_id, last_n_games
        )

        if not data:
            logger.warning(f"Insufficient data for {player_name}")
            return self._empty_result(player_name, prop_type, prop_line, "Insufficient data")

        # Izračunaj sve faktore
        factors = {}

        # 1. Recent Form (25%)
        factors['recent_form'] = self._calculate_recent_form_factor(
            data['game_log'], stat_column, last_n_games, prop_line
        )

        # 2. Opponent Matchup (20%)
        factors['opponent_matchup'] = self._calculate_opponent_matchup_factor(
            data['vs_opponent'], stat_column, prop_line
        )

        # 3. Home/Away Split (15%)
        factors['home_away_split'] = self._calculate_home_away_factor(
            data['splits'], stat_column, is_home_game, prop_line
        )

        # 4. Opponent Defense (20%)
        factors['opponent_defense'] = self._calculate_opponent_defense_factor(
            data['opponent_defense'], opponent_team_id, prop_type
        )

        # 5. Pace Factor (10%)
        factors['pace_factor'] = self._calculate_pace_factor(
            data['team_pace'], data['opponent_pace']
        )

        # 6. Usage Factor (10%)
        factors['usage_factor'] = self._calculate_usage_factor(
            data['game_log'], last_n_games
        )

        # Izračunaj finalni confidence score
        confidence_score = self._calculate_confidence_score(factors)

        # Projektiraj očekivanu vrijednost
        projected_value = self._project_stat_value(
            data['game_log'], stat_column, last_n_games, factors
        )

        # Generiši preporuku
        recommendation = get_recommendation(confidence_score, prop_line, projected_value)
        confidence_label = get_confidence_label(confidence_score)

        # Pripremi detaljan rezultat
        result = {
            'player_id': player_id,
            'player_name': player_name,
            'team_id': team_id,
            'opponent_team_id': opponent_team_id,
            'prop_type': prop_type,
            'prop_line': prop_line,
            'projected_value': round(projected_value, 1),
            'edge': round(projected_value - prop_line, 1),
            'edge_pct': round((projected_value - prop_line) / prop_line * 100, 1) if prop_line > 0 else 0,
            'confidence_score': round(confidence_score, 3),
            'confidence_label': confidence_label,
            'recommendation': recommendation,
            'is_home_game': is_home_game,
            'factors': {
                'recent_form': round(factors['recent_form']['score'], 3),
                'opponent_matchup': round(factors['opponent_matchup']['score'], 3),
                'home_away_split': round(factors['home_away_split']['score'], 3),
                'opponent_defense': round(factors['opponent_defense']['score'], 3),
                'pace_factor': round(factors['pace_factor']['score'], 3),
                'usage_factor': round(factors['usage_factor']['score'], 3),
            },
            'details': {
                'recent_form': factors['recent_form']['details'],
                'opponent_matchup': factors['opponent_matchup']['details'],
                'home_away_split': factors['home_away_split']['details'],
                'opponent_defense': factors['opponent_defense']['details'],
                'pace': factors['pace_factor']['details'],
                'usage': factors['usage_factor']['details'],
            }
        }

        logger.info(
            f"Analysis complete: {recommendation} "
            f"(Confidence: {confidence_score:.1%}, Projected: {projected_value:.1f})"
        )

        return result

    # ============================================================================
    # DATA FETCHING
    # ============================================================================

    def _fetch_all_data(
        self, player_id: int, team_id: int, opponent_team_id: int, last_n_games: int
    ) -> Optional[Dict]:
        """Dohvati sve potrebne podatke odjednom"""
        try:
            data = {}

            # Player game log
            data['game_log'] = self.fetcher.get_player_game_log(player_id, last_n_games * 2)
            if data['game_log'].empty:
                logger.warning(f"No game log data for player {player_id}")
                return None

            # Player splits
            data['splits'] = self.fetcher.get_player_splits(player_id)

            # Player vs opponent
            data['vs_opponent'] = self.fetcher.get_player_vs_opponent(player_id, opponent_team_id)

            # Opponent defense stats
            data['opponent_defense'] = self.fetcher.get_league_team_defense_stats()

            # Team pace
            data['team_pace'] = self.fetcher.get_pace_for_team(team_id)

            # Opponent pace
            data['opponent_pace'] = self.fetcher.get_pace_for_team(opponent_team_id)

            return data

        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return None

    # ============================================================================
    # FACTOR CALCULATIONS
    # ============================================================================

    def _calculate_recent_form_factor(
        self, game_log: pd.DataFrame, stat_column: str, last_n: int, prop_line: float
    ) -> Dict:
        """Izračunaj faktor za recent form"""
        try:
            if game_log.empty or stat_column not in game_log.columns:
                return {'score': 0.5, 'details': {}}

            # Prosjek zadnjih N utakmica
            recent_avg = calculate_average(game_log, stat_column, last_n)

            # Konzistentnost (% utakmica preko linije)
            consistency = calculate_consistency(game_log, stat_column, prop_line, last_n)

            # Trend
            trend = calculate_trend(game_log, stat_column, min(5, last_n))

            # Standard deviation (manji = konzistentniji)
            std_dev = calculate_std_deviation(game_log, stat_column, last_n)
            consistency_score = max(0, 1 - (std_dev / recent_avg)) if recent_avg > 0 else 0

            # Score kalkulacija
            # Ako recent avg >> prop line = high score
            # Ako konzistentnost visoka = bonus
            avg_score = normalize_score(recent_avg, prop_line * 0.5, prop_line * 1.5)

            # Kombinuj avg i konzistentnost
            score = (avg_score * 0.6) + (consistency * 0.3) + (consistency_score * 0.1)

            # Trend adjustment
            if trend == 'up':
                score *= 1.1  # 10% bonus
            elif trend == 'down':
                score *= 0.9  # 10% penalizacija

            score = max(0, min(1, score))  # Clamp 0-1

            return {
                'score': score,
                'details': {
                    'recent_avg': round(recent_avg, 1),
                    'consistency_pct': round(consistency * 100, 1),
                    'trend': trend,
                    'std_dev': round(std_dev, 2),
                    'games_analyzed': min(len(game_log), last_n)
                }
            }

        except Exception as e:
            logger.error(f"Error calculating recent form: {e}")
            return {'score': 0.5, 'details': {}}

    def _calculate_opponent_matchup_factor(
        self, vs_opponent: pd.DataFrame, stat_column: str, prop_line: float
    ) -> Dict:
        """Izračunaj faktor za opponent matchup"""
        try:
            if vs_opponent.empty or stat_column not in vs_opponent.columns:
                # Nema historije - neutralan score
                return {
                    'score': 0.5,
                    'details': {'vs_opponent_avg': 0, 'games': 0, 'note': 'No history'}
                }

            vs_avg = float(vs_opponent[stat_column].iloc[0])
            games = int(vs_opponent['GP'].iloc[0]) if 'GP' in vs_opponent.columns else 0

            # Normaliziraj score
            score = normalize_score(vs_avg, prop_line * 0.5, prop_line * 1.5)

            # Ako ima malo utakmica, manje težine
            if games < 3:
                score = (score * 0.5) + (0.5 * 0.5)  # Blend sa neutral

            return {
                'score': score,
                'details': {
                    'vs_opponent_avg': round(vs_avg, 1),
                    'games': games
                }
            }

        except Exception as e:
            logger.error(f"Error calculating opponent matchup: {e}")
            return {'score': 0.5, 'details': {}}

    def _calculate_home_away_factor(
        self, splits: Dict, stat_column: str, is_home: bool, prop_line: float
    ) -> Dict:
        """Izračunaj faktor za home/away split"""
        try:
            if not splits or 'location' not in splits or splits['location'].empty:
                return {'score': 0.5, 'details': {}}

            location_df = splits['location']

            # Filtriraj home/away
            if is_home:
                row = location_df[location_df['GROUP_VALUE'] == 'Home']
            else:
                row = location_df[location_df['GROUP_VALUE'] == 'Road']

            if row.empty or stat_column not in row.columns:
                return {'score': 0.5, 'details': {}}

            location_avg = float(row[stat_column].iloc[0])
            games = int(row['GP'].iloc[0]) if 'GP' in row.columns else 0

            # Normaliziraj score
            score = normalize_score(location_avg, prop_line * 0.5, prop_line * 1.5)

            return {
                'score': score,
                'details': {
                    'location': 'Home' if is_home else 'Away',
                    'location_avg': round(location_avg, 1),
                    'games': games
                }
            }

        except Exception as e:
            logger.error(f"Error calculating home/away factor: {e}")
            return {'score': 0.5, 'details': {}}

    def _calculate_opponent_defense_factor(
        self, defense_df: pd.DataFrame, opponent_team_id: int, prop_type: str
    ) -> Dict:
        """Izračunaj faktor za opponent defense"""
        try:
            if defense_df.empty:
                return {'score': 0.5, 'details': {}}

            # Filtriraj za opponent tim
            opp_def = defense_df[defense_df['TEAM_ID'] == opponent_team_id]

            if opp_def.empty:
                return {'score': 0.5, 'details': {}}

            # Mapiranje prop types na defensive stats
            def_stat_map = {
                'points': 'OPP_PTS',  # Points allowed
                'rebounds': 'OPP_REB',  # Rebounds allowed
                'assists': 'OPP_AST',  # Assists allowed
                'threes': 'OPP_FG3M',  # 3PT made allowed
            }

            stat_col = def_stat_map.get(prop_type, 'DEF_RATING')

            if stat_col not in opp_def.columns and 'DEF_RATING' in opp_def.columns:
                stat_col = 'DEF_RATING'

            if stat_col not in opp_def.columns:
                return {'score': 0.5, 'details': {}}

            opp_def_value = float(opp_def[stat_col].iloc[0])

            # Za defensive stats - VEĆA vrijednost = LOŠIJA obrana = BOLJI prop
            # Normaliziraj na osnovu league average
            league_avg = float(defense_df[stat_col].mean())
            league_std = float(defense_df[stat_col].std())

            # Z-score
            z_score = (opp_def_value - league_avg) / league_std if league_std > 0 else 0

            # Konvertuj z-score u 0-1 score (higher defense value = higher score)
            # z_score od -2 do +2 mapiramo na 0 do 1
            score = normalize_score(z_score, -2, 2)

            # Dohvati rank
            rank = int(opp_def['DEF_RATING'].rank(ascending=True).iloc[0]) if 'DEF_RATING' in opp_def.columns else 0

            return {
                'score': score,
                'details': {
                    'opponent_def_value': round(opp_def_value, 1),
                    'league_avg': round(league_avg, 1),
                    'defensive_rank': rank
                }
            }

        except Exception as e:
            logger.error(f"Error calculating opponent defense: {e}")
            return {'score': 0.5, 'details': {}}

    def _calculate_pace_factor(self, team_pace: float, opponent_pace: float) -> Dict:
        """Izračunaj faktor za pace"""
        try:
            # Prosječan pace
            avg_pace = (team_pace + opponent_pace) / 2

            # League average je ~100
            league_avg_pace = 100.0

            # Brži pace = više posesija = veća šansa za stats
            # Normaliziraj pace (90-110 range tipično)
            score = normalize_score(avg_pace, 90, 110)

            return {
                'score': score,
                'details': {
                    'team_pace': round(team_pace, 1),
                    'opponent_pace': round(opponent_pace, 1),
                    'avg_pace': round(avg_pace, 1),
                    'vs_league_avg': round(avg_pace - league_avg_pace, 1)
                }
            }

        except Exception as e:
            logger.error(f"Error calculating pace: {e}")
            return {'score': 0.5, 'details': {}}

    def _calculate_usage_factor(self, game_log: pd.DataFrame, last_n: int) -> Dict:
        """Izračunaj faktor za usage (prilagođen za injuries)"""
        try:
            if game_log.empty or 'MIN' not in game_log.columns:
                return {'score': 0.5, 'details': {}}

            # Prosjek minuta zadnjih N utakmica
            recent_min = calculate_average(game_log, 'MIN', last_n)

            # Ukupan prosjek minuta
            overall_min = calculate_average(game_log, 'MIN', None)

            # Ako igrač igra VIŠE minuta sada nego prije = higher usage
            min_trend = calculate_trend(game_log, 'MIN', min(5, last_n))

            # Normaliziraj minute (20-40 range)
            score = normalize_score(recent_min, 20, 40)

            # Trend adjustment
            if min_trend == 'up':
                score *= 1.1
            elif min_trend == 'down':
                score *= 0.9

            score = max(0, min(1, score))

            return {
                'score': score,
                'details': {
                    'recent_min': round(recent_min, 1),
                    'overall_min': round(overall_min, 1),
                    'min_trend': min_trend
                }
            }

        except Exception as e:
            logger.error(f"Error calculating usage: {e}")
            return {'score': 0.5, 'details': {}}

    # ============================================================================
    # FINAL SCORING
    # ============================================================================

    def _calculate_confidence_score(self, factors: Dict) -> float:
        """
        Izračunaj finalni confidence score kombinujući sve faktore sa weights

        Args:
            factors: Dict sa svim faktorima i njihovim scores

        Returns:
            Confidence score (0-1)
        """
        total_score = 0.0

        for factor_name, weight in self.weights.items():
            if factor_name in factors:
                factor_score = factors[factor_name]['score']
                total_score += factor_score * weight

        return total_score

    def _project_stat_value(
        self, game_log: pd.DataFrame, stat_column: str, last_n: int, factors: Dict
    ) -> float:
        """
        Projektiraj očekivanu stat vrijednost

        Args:
            game_log: Game log DataFrame
            stat_column: Stat kolona
            last_n: Broj utakmica
            factors: Svi faktori

        Returns:
            Projektivna vrijednost
        """
        try:
            if game_log.empty or stat_column not in game_log.columns:
                return 0.0

            # Baseline - recent average
            baseline = calculate_average(game_log, stat_column, last_n)

            # Adjustments na osnovu faktora
            # Svaki faktor može povećati ili smanjiti baseline

            adjustment_multiplier = 1.0

            # Home/Away adjustment
            home_away_score = factors['home_away_split']['score']
            if home_away_score > 0.6:
                adjustment_multiplier *= 1.05  # 5% boost
            elif home_away_score < 0.4:
                adjustment_multiplier *= 0.95  # 5% reduction

            # Opponent matchup adjustment
            opp_score = factors['opponent_matchup']['score']
            if opp_score > 0.6:
                adjustment_multiplier *= 1.05
            elif opp_score < 0.4:
                adjustment_multiplier *= 0.95

            # Defense adjustment
            def_score = factors['opponent_defense']['score']
            if def_score > 0.6:
                adjustment_multiplier *= 1.08  # 8% boost za slabu obranu
            elif def_score < 0.4:
                adjustment_multiplier *= 0.92  # 8% reduction za jaku obranu

            # Pace adjustment
            pace_score = factors['pace_factor']['score']
            if pace_score > 0.6:
                adjustment_multiplier *= 1.03
            elif pace_score < 0.4:
                adjustment_multiplier *= 0.97

            # Usage adjustment
            usage_score = factors['usage_factor']['score']
            if usage_score > 0.6:
                adjustment_multiplier *= 1.03
            elif usage_score < 0.4:
                adjustment_multiplier *= 0.97

            projected = baseline * adjustment_multiplier

            return projected

        except Exception as e:
            logger.error(f"Error projecting stat value: {e}")
            return 0.0

    # ============================================================================
    # HELPERS
    # ============================================================================

    def _empty_result(self, player_name: str, prop_type: str, prop_line: float, reason: str) -> Dict:
        """Return empty result kada nema podataka"""
        return {
            'player_name': player_name,
            'prop_type': prop_type,
            'prop_line': prop_line,
            'confidence_score': 0.0,
            'confidence_label': 'very_low',
            'recommendation': 'PASS',
            'error': reason,
            'factors': {},
            'details': {}
        }
