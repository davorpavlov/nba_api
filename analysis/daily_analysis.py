"""
Glavna skripta za dnevnu NBA analizu i props picking
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
import json
import os

from .wrappers import NBADataFetcher
from .scoring_model import PropsScoringModel
from .config import (
    CURRENT_SEASON,
    PROPS_TYPES,
    DEFAULT_GAMES_SAMPLE,
    OUTPUT_DIR,
    CONFIDENCE_LEVELS
)
from .utils import logger, format_output

logger = logging.getLogger(__name__)


class DailyAnalysis:
    """
    Klasa za pokretanje dnevne analize NBA props-a
    """

    def __init__(self, season: str = CURRENT_SEASON):
        """
        Args:
            season: NBA sezona (default: current)
        """
        self.season = season
        self.fetcher = NBADataFetcher(season=season)
        self.scoring_model = PropsScoringModel(self.fetcher)
        logger.info(f"DailyAnalysis initialized for season {season}")

    def run_daily_analysis(
        self,
        prop_types: Optional[List[str]] = None,
        min_confidence: float = 0.60,
        top_n: Optional[int] = None
    ) -> List[Dict]:
        """
        Pokreni kompletnu dnevnu analizu

        Args:
            prop_types: Lista prop types za analizu (None = svi)
            min_confidence: Minimalni confidence score za prikaz
            top_n: Broj top pickova za vratiti (None = svi)

        Returns:
            Lista sa analiziranim props-ima sortirana po confidence score-u
        """
        logger.info("Starting daily analysis...")

        # 1. Dohvati današnje utakmice
        todays_games = self.fetcher.get_todays_games()

        if not todays_games:
            logger.warning("No games found for today")
            return []

        logger.info(f"Found {len(todays_games)} games today")

        # 2. Pripremi prop types za analizu
        if prop_types is None:
            prop_types = list(PROPS_TYPES.keys())

        # 3. Analiziraj sve props
        all_props = []

        for game in todays_games:
            logger.info(
                f"Analyzing game: {game['away_team']} @ {game['home_team']}"
            )

            # Analiziraj home tim
            home_props = self._analyze_team_props(
                game['home_team_id'],
                game['away_team_id'],
                True,  # is_home
                prop_types
            )
            all_props.extend(home_props)

            # Analiziraj away tim
            away_props = self._analyze_team_props(
                game['away_team_id'],
                game['home_team_id'],
                False,  # is_home
                prop_types
            )
            all_props.extend(away_props)

        # 4. Filtriraj po confidence-u
        filtered_props = [
            p for p in all_props
            if p.get('confidence_score', 0) >= min_confidence
        ]

        # 5. Sortiraj po confidence score-u
        filtered_props.sort(
            key=lambda x: x.get('confidence_score', 0),
            reverse=True
        )

        # 6. Uzmi top N
        if top_n:
            filtered_props = filtered_props[:top_n]

        logger.info(
            f"Analysis complete: {len(filtered_props)} props above "
            f"{min_confidence:.0%} confidence"
        )

        return filtered_props

    def analyze_specific_player_props(
        self,
        player_name: str,
        opponent_team_name: str,
        is_home_game: bool,
        props_to_analyze: Dict[str, float]
    ) -> List[Dict]:
        """
        Analiziraj specifične props za jednog igrača

        Args:
            player_name: Ime igrača
            opponent_team_name: Ime protivničkog tima
            is_home_game: Da li je home utakmica
            props_to_analyze: Dict sa prop types i linijama
                              npr. {'points': 28.5, 'rebounds': 7.5, 'assists': 6.5}

        Returns:
            Lista rezultata analize

        Example:
            >>> analysis = DailyAnalysis()
            >>> results = analysis.analyze_specific_player_props(
            ...     player_name='LeBron James',
            ...     opponent_team_name='Golden State Warriors',
            ...     is_home_game=True,
            ...     props_to_analyze={
            ...         'points': 25.5,
            ...         'rebounds': 7.5,
            ...         'assists': 7.5
            ...     }
            ... )
        """
        logger.info(f"Analyzing props for {player_name}")

        # Dohvati player i team info
        player = self.fetcher.get_player_by_name(player_name)
        if not player:
            logger.error(f"Player not found: {player_name}")
            return []

        opponent = self.fetcher.get_team_by_name(opponent_team_name)
        if not opponent:
            logger.error(f"Opponent team not found: {opponent_team_name}")
            return []

        # Dohvati player's team (potrebno za team_id)
        # Pretpostavljamo da player dict ima team_id (može varirati)
        # Alternativa: dohvati preko roster search
        roster_teams = self._find_player_team(player['id'])
        if not roster_teams:
            logger.error(f"Could not find team for {player_name}")
            return []

        team_id = roster_teams[0]

        # Analiziraj svaki prop
        results = []

        for prop_type, prop_line in props_to_analyze.items():
            if prop_type not in PROPS_TYPES:
                logger.warning(f"Invalid prop type: {prop_type}")
                continue

            result = self.scoring_model.analyze_player_prop(
                player_id=player['id'],
                player_name=player['full_name'],
                team_id=team_id,
                opponent_team_id=opponent['id'],
                prop_type=prop_type,
                prop_line=prop_line,
                is_home_game=is_home_game,
                last_n_games=DEFAULT_GAMES_SAMPLE
            )

            results.append(result)

        return results

    def export_results(
        self,
        results: List[Dict],
        output_format: str = 'json',
        filename: Optional[str] = None
    ) -> str:
        """
        Exportuj rezultate u fajl

        Args:
            results: Lista rezultata
            output_format: 'json', 'csv', ili 'excel'
            filename: Ime fajla (None = auto-generiši)

        Returns:
            Path do kreirianog fajla
        """
        # Kreiraj output directory ako ne postoji
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Auto-generiši filename ako nije dat
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"nba_props_analysis_{timestamp}"

        filepath = os.path.join(OUTPUT_DIR, filename)

        try:
            if output_format == 'json':
                filepath += '.json'
                with open(filepath, 'w') as f:
                    json.dump(results, f, indent=2)

            elif output_format == 'csv':
                filepath += '.csv'
                df = pd.DataFrame(results)
                df.to_csv(filepath, index=False)

            elif output_format == 'excel':
                filepath += '.xlsx'
                df = pd.DataFrame(results)
                df.to_excel(filepath, index=False)

            else:
                logger.error(f"Invalid output format: {output_format}")
                return ""

            logger.info(f"Results exported to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error exporting results: {e}")
            return ""

    def print_results(self, results: List[Dict], detailed: bool = False):
        """
        Printaj rezultate u konzolu

        Args:
            results: Lista rezultata
            detailed: Da li prikazati detaljne faktore
        """
        if not results:
            print("No results to display")
            return

        print("\n" + "="*80)
        print(f"NBA PROPS ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*80 + "\n")

        for i, r in enumerate(results, 1):
            print(f"{i}. {r.get('player_name', 'Unknown')} - {r.get('prop_type', 'N/A').upper()}")
            print(f"   Line: {r.get('prop_line', 0):.1f} | Projected: {r.get('projected_value', 0):.1f} | Edge: {r.get('edge', 0):+.1f} ({r.get('edge_pct', 0):+.1f}%)")
            print(f"   Recommendation: {r.get('recommendation', 'PASS')} | Confidence: {r.get('confidence_score', 0):.1%} ({r.get('confidence_label', 'N/A')})")

            if detailed and 'factors' in r:
                print(f"   Factors:")
                for factor, score in r['factors'].items():
                    print(f"     - {factor}: {score:.1%}")

            print()

        print("="*80 + "\n")

    # ============================================================================
    # PRIVATE METHODS
    # ============================================================================

    def _analyze_team_props(
        self,
        team_id: int,
        opponent_team_id: int,
        is_home: bool,
        prop_types: List[str]
    ) -> List[Dict]:
        """Analiziraj props za sve igrače u timu"""
        results = []

        try:
            # Dohvati roster
            roster = self.fetcher.get_team_roster(team_id)

            if roster.empty:
                logger.warning(f"No roster found for team {team_id}")
                return results

            # Analiziraj top igrače (npr. starters ili top 8 po minutima)
            # Za demo, analiziraj sve, ali u produkciji možeš filtrirati
            top_players = roster.head(8)  # Top 8 igrača

            for _, player_row in top_players.iterrows():
                player_id = int(player_row['PLAYER_ID'])
                player_name = player_row['PLAYER']

                # Analiziraj svaki prop type
                for prop_type in prop_types:
                    # Automatski odredi prop line (za demo - u produkciji koristiš stvarne linije)
                    prop_line = self._estimate_prop_line(player_id, prop_type)

                    if prop_line == 0:
                        continue  # Skip ako nema dovoljno podataka

                    try:
                        result = self.scoring_model.analyze_player_prop(
                            player_id=player_id,
                            player_name=player_name,
                            team_id=team_id,
                            opponent_team_id=opponent_team_id,
                            prop_type=prop_type,
                            prop_line=prop_line,
                            is_home_game=is_home,
                            last_n_games=DEFAULT_GAMES_SAMPLE
                        )

                        results.append(result)

                    except Exception as e:
                        logger.error(f"Error analyzing {player_name} {prop_type}: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error analyzing team props: {e}")

        return results

    def _estimate_prop_line(self, player_id: int, prop_type: str) -> float:
        """
        Procijeni prop liniju na osnovu recent average
        (U produkciji, koristiš stvarne betting linije)
        """
        try:
            game_log = self.fetcher.get_player_game_log(player_id, 10)

            if game_log.empty:
                return 0.0

            prop_config = PROPS_TYPES.get(prop_type)
            if not prop_config:
                return 0.0

            stat_column = prop_config['stat_column']

            if stat_column not in game_log.columns:
                return 0.0

            # Procijeni liniju kao recent average
            avg = float(game_log[stat_column].head(10).mean())

            # Zaokruži na 0.5
            estimated_line = round(avg * 2) / 2

            return estimated_line if estimated_line > 0 else 0.0

        except Exception as e:
            logger.error(f"Error estimating prop line: {e}")
            return 0.0

    def _find_player_team(self, player_id: int) -> List[int]:
        """Pronađi team_id za igrača (pretraži sve timove)"""
        try:
            from nba_api.stats.static import teams as static_teams

            all_teams = static_teams.get_teams()

            player_teams = []

            for team in all_teams:
                roster = self.fetcher.get_team_roster(team['id'])

                if not roster.empty and 'PLAYER_ID' in roster.columns:
                    if player_id in roster['PLAYER_ID'].values:
                        player_teams.append(team['id'])

            return player_teams

        except Exception as e:
            logger.error(f"Error finding player team: {e}")
            return []


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Glavni CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description='NBA Props Daily Analysis')

    parser.add_argument(
        '--season',
        type=str,
        default=CURRENT_SEASON,
        help='NBA season (e.g., 2024-25)'
    )

    parser.add_argument(
        '--prop-types',
        type=str,
        nargs='+',
        default=None,
        help='Prop types to analyze (e.g., points rebounds assists)'
    )

    parser.add_argument(
        '--min-confidence',
        type=float,
        default=0.60,
        help='Minimum confidence score (0-1)'
    )

    parser.add_argument(
        '--top-n',
        type=int,
        default=None,
        help='Number of top picks to show'
    )

    parser.add_argument(
        '--output',
        type=str,
        choices=['json', 'csv', 'excel', 'console'],
        default='console',
        help='Output format'
    )

    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed factor breakdown'
    )

    args = parser.parse_args()

    # Pokreni analizu
    analysis = DailyAnalysis(season=args.season)

    results = analysis.run_daily_analysis(
        prop_types=args.prop_types,
        min_confidence=args.min_confidence,
        top_n=args.top_n
    )

    # Output
    if args.output == 'console':
        analysis.print_results(results, detailed=args.detailed)
    else:
        filepath = analysis.export_results(results, output_format=args.output)
        print(f"Results exported to: {filepath}")


if __name__ == '__main__':
    main()
