"""
NBA API Wrapper funkcije za lakše preuzimanje podataka
"""

import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
from datetime import datetime, timedelta

# NBA API imports
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import (
    playergamelog,
    playerdashboardbygeneralsplits,
    playerdashboardbyopponent,
    teamdashboardbygeneralsplits,
    teamdashboardbyopponent,
    leaguedashteamstats,
    leaguedashplayerstats,
    shotchartdetail,
    boxscoreusagev2,
    playerdashptpass,
    playerdashptreb,
    commonteamroster,
    leaguegamefinder,
    playervsplayer,
)

try:
    from nba_api.live.nba.endpoints import scoreboard, boxscore
    LIVE_API_AVAILABLE = True
except ImportError:
    LIVE_API_AVAILABLE = False
    logging.warning("Live NBA API not available")

from .config import CURRENT_SEASON, API_TIMEOUT, DEFAULT_GAMES_SAMPLE
from .utils import safe_api_call, logger

logger = logging.getLogger(__name__)


class NBADataFetcher:
    """
    Wrapper klasa za jednostavno preuzimanje NBA podataka
    """

    def __init__(self, season: str = CURRENT_SEASON, timeout: int = API_TIMEOUT):
        self.season = season
        self.timeout = timeout
        logger.info(f"NBADataFetcher initialized for season {season}")

    # ============================================================================
    # STATIC DATA (bez API poziva)
    # ============================================================================

    def get_player_by_name(self, name: str) -> Optional[Dict]:
        """
        Pronađi igrača po imenu

        Args:
            name: Ime igrača (full name ili partial)

        Returns:
            Dict sa player info ili None
        """
        try:
            player_list = players.find_players_by_full_name(name)
            if player_list:
                return player_list[0]

            # Pokušaj partial match
            all_players = players.get_players()
            for p in all_players:
                if name.lower() in p['full_name'].lower():
                    return p

            logger.warning(f"Player not found: {name}")
            return None
        except Exception as e:
            logger.error(f"Error finding player {name}: {e}")
            return None

    def get_team_by_name(self, name: str) -> Optional[Dict]:
        """
        Pronađi tim po imenu

        Args:
            name: Ime tima ili abbreviation

        Returns:
            Dict sa team info ili None
        """
        try:
            team_list = teams.find_teams_by_full_name(name)
            if team_list:
                return team_list[0]

            # Pokušaj abbreviation
            team_list = teams.find_team_by_abbreviation(name.upper())
            if team_list:
                return team_list

            logger.warning(f"Team not found: {name}")
            return None
        except Exception as e:
            logger.error(f"Error finding team {name}: {e}")
            return None

    # ============================================================================
    # LIVE DATA
    # ============================================================================

    def get_todays_games(self) -> List[Dict]:
        """
        Dohvati sve današnje utakmice

        Returns:
            Lista utakmica sa osnovnim info
        """
        if not LIVE_API_AVAILABLE:
            logger.warning("Live API not available, using scoreboard fallback")
            return []

        try:
            board = scoreboard.ScoreBoard()
            games_data = board.get_dict()

            games = []
            if 'scoreboard' in games_data and 'games' in games_data['scoreboard']:
                for game in games_data['scoreboard']['games']:
                    games.append({
                        'game_id': game.get('gameId'),
                        'game_code': game.get('gameCode'),
                        'status': game.get('gameStatus'),
                        'status_text': game.get('gameStatusText'),
                        'home_team': game.get('homeTeam', {}).get('teamName'),
                        'home_team_id': game.get('homeTeam', {}).get('teamId'),
                        'away_team': game.get('awayTeam', {}).get('teamName'),
                        'away_team_id': game.get('awayTeam', {}).get('teamId'),
                        'home_score': game.get('homeTeam', {}).get('score', 0),
                        'away_score': game.get('awayTeam', {}).get('score', 0),
                    })

            logger.info(f"Found {len(games)} games today")
            return games

        except Exception as e:
            logger.error(f"Error fetching today's games: {e}")
            return []

    # ============================================================================
    # PLAYER DATA
    # ============================================================================

    def get_player_game_log(self, player_id: int, last_n: Optional[int] = None) -> pd.DataFrame:
        """
        Dohvati game log za igrača

        Args:
            player_id: NBA player ID
            last_n: Broj zadnjih utakmica (None = sve)

        Returns:
            DataFrame sa game log podacima
        """
        try:
            logger.info(f"Fetching game log for player {player_id}")

            gamelog = safe_api_call(
                playergamelog.PlayerGameLog,
                player_id=str(player_id),
                season=self.season,
                timeout=self.timeout
            )

            if gamelog is None:
                return pd.DataFrame()

            df = gamelog.get_data_frames()[0]

            if last_n and not df.empty:
                df = df.head(last_n)

            logger.info(f"Retrieved {len(df)} games for player {player_id}")
            return df

        except Exception as e:
            logger.error(f"Error fetching game log for player {player_id}: {e}")
            return pd.DataFrame()

    def get_player_splits(self, player_id: int) -> Dict[str, pd.DataFrame]:
        """
        Dohvati split statistike za igrača (Home/Away, Last N games, etc.)

        Args:
            player_id: NBA player ID

        Returns:
            Dict sa različitim split DataFrames
        """
        try:
            logger.info(f"Fetching splits for player {player_id}")

            splits = safe_api_call(
                playerdashboardbygeneralsplits.PlayerDashboardByGeneralSplits,
                player_id=str(player_id),
                season=self.season,
                timeout=self.timeout
            )

            if splits is None:
                return {}

            dfs = splits.get_data_frames()

            result = {}
            dataset_names = [
                'overall', 'location', 'wins_losses', 'month',
                'pre_post_all_star', 'starting_position', 'days_rest'
            ]

            for i, name in enumerate(dataset_names):
                if i < len(dfs):
                    result[name] = dfs[i]

            logger.info(f"Retrieved {len(result)} split datasets for player {player_id}")
            return result

        except Exception as e:
            logger.error(f"Error fetching splits for player {player_id}: {e}")
            return {}

    def get_player_vs_opponent(self, player_id: int, opponent_team_id: Optional[int] = None) -> pd.DataFrame:
        """
        Dohvati statistike igrača protiv određenog tima

        Args:
            player_id: NBA player ID
            opponent_team_id: Opponent team ID (None = protiv svih timova)

        Returns:
            DataFrame sa opponent stats
        """
        try:
            logger.info(f"Fetching opponent stats for player {player_id}")

            vs_opp = safe_api_call(
                playerdashboardbyopponent.PlayerDashboardByOpponent,
                player_id=str(player_id),
                season=self.season,
                timeout=self.timeout
            )

            if vs_opp is None:
                return pd.DataFrame()

            df = vs_opp.get_data_frames()[0]

            # Filter za specifičan tim ako je naveden
            if opponent_team_id and not df.empty and 'OPPONENT_TEAM_ID' in df.columns:
                df = df[df['OPPONENT_TEAM_ID'] == opponent_team_id]

            logger.info(f"Retrieved opponent stats for player {player_id}")
            return df

        except Exception as e:
            logger.error(f"Error fetching opponent stats for player {player_id}: {e}")
            return pd.DataFrame()

    def get_player_head_to_head(self, player_id: int, vs_player_id: int) -> pd.DataFrame:
        """
        Dohvati head-to-head statistike između dva igrača

        Args:
            player_id: NBA player ID
            vs_player_id: Opponent player ID

        Returns:
            DataFrame sa H2H stats
        """
        try:
            logger.info(f"Fetching H2H: {player_id} vs {vs_player_id}")

            h2h = safe_api_call(
                playervsplayer.PlayerVsPlayer,
                player_id=str(player_id),
                vs_player_id=str(vs_player_id),
                season=self.season,
                timeout=self.timeout
            )

            if h2h is None:
                return pd.DataFrame()

            df = h2h.get_data_frames()[0]
            logger.info(f"Retrieved H2H stats")
            return df

        except Exception as e:
            logger.error(f"Error fetching H2H stats: {e}")
            return pd.DataFrame()

    def get_player_shot_chart(self, player_id: int, team_id: int) -> pd.DataFrame:
        """
        Dohvati shot chart podatke za igrača

        Args:
            player_id: NBA player ID
            team_id: Team ID

        Returns:
            DataFrame sa shot chart podacima (lokacije, zone, FG%)
        """
        try:
            logger.info(f"Fetching shot chart for player {player_id}")

            shots = safe_api_call(
                shotchartdetail.ShotChartDetail,
                player_id=str(player_id),
                team_id=str(team_id),
                season_nullable=self.season,
                context_measure_simple='FGA',
                timeout=self.timeout
            )

            if shots is None:
                return pd.DataFrame()

            df = shots.get_data_frames()[0]
            logger.info(f"Retrieved {len(df)} shots for player {player_id}")
            return df

        except Exception as e:
            logger.error(f"Error fetching shot chart for player {player_id}: {e}")
            return pd.DataFrame()

    def get_player_passing_stats(self, player_id: int, team_id: int) -> pd.DataFrame:
        """
        Dohvati passing/playmaking statistike (za assists props)

        Args:
            player_id: NBA player ID
            team_id: Team ID

        Returns:
            DataFrame sa passing stats
        """
        try:
            logger.info(f"Fetching passing stats for player {player_id}")

            passing = safe_api_call(
                playerdashptpass.PlayerDashPtPass,
                player_id=str(player_id),
                team_id=str(team_id),
                season=self.season,
                timeout=self.timeout
            )

            if passing is None:
                return pd.DataFrame()

            df = passing.get_data_frames()[0]
            logger.info(f"Retrieved passing stats for player {player_id}")
            return df

        except Exception as e:
            logger.error(f"Error fetching passing stats for player {player_id}: {e}")
            return pd.DataFrame()

    def get_player_rebounding_stats(self, player_id: int, team_id: int) -> pd.DataFrame:
        """
        Dohvati rebounding tracking statistike (za rebounds props)

        Args:
            player_id: NBA player ID
            team_id: Team ID

        Returns:
            DataFrame sa rebounding stats
        """
        try:
            logger.info(f"Fetching rebounding stats for player {player_id}")

            rebounds = safe_api_call(
                playerdashptreb.PlayerDashPtReb,
                player_id=str(player_id),
                team_id=str(team_id),
                season=self.season,
                timeout=self.timeout
            )

            if rebounds is None:
                return pd.DataFrame()

            df = rebounds.get_data_frames()[0]
            logger.info(f"Retrieved rebounding stats for player {player_id}")
            return df

        except Exception as e:
            logger.error(f"Error fetching rebounding stats for player {player_id}: {e}")
            return pd.DataFrame()

    # ============================================================================
    # TEAM DATA
    # ============================================================================

    def get_team_splits(self, team_id: int) -> Dict[str, pd.DataFrame]:
        """
        Dohvati team split statistike (Home/Away, Last N, etc.)

        Args:
            team_id: NBA team ID

        Returns:
            Dict sa različitim split DataFrames
        """
        try:
            logger.info(f"Fetching splits for team {team_id}")

            splits = safe_api_call(
                teamdashboardbygeneralsplits.TeamDashboardByGeneralSplits,
                team_id=str(team_id),
                season=self.season,
                timeout=self.timeout
            )

            if splits is None:
                return {}

            dfs = splits.get_data_frames()

            result = {}
            dataset_names = ['overall', 'location', 'wins_losses', 'month', 'pre_post_all_star']

            for i, name in enumerate(dataset_names):
                if i < len(dfs):
                    result[name] = dfs[i]

            logger.info(f"Retrieved {len(result)} split datasets for team {team_id}")
            return result

        except Exception as e:
            logger.error(f"Error fetching splits for team {team_id}: {e}")
            return {}

    def get_team_vs_opponent(self, team_id: int, opponent_team_id: Optional[int] = None) -> pd.DataFrame:
        """
        Dohvati team statistike protiv određenog protivnika

        Args:
            team_id: NBA team ID
            opponent_team_id: Opponent team ID (None = protiv svih)

        Returns:
            DataFrame sa opponent stats
        """
        try:
            logger.info(f"Fetching opponent stats for team {team_id}")

            vs_opp = safe_api_call(
                teamdashboardbyopponent.TeamDashboardByOpponent,
                team_id=str(team_id),
                season=self.season,
                timeout=self.timeout
            )

            if vs_opp is None:
                return pd.DataFrame()

            df = vs_opp.get_data_frames()[0]

            if opponent_team_id and not df.empty and 'OPPONENT_TEAM_ID' in df.columns:
                df = df[df['OPPONENT_TEAM_ID'] == opponent_team_id]

            logger.info(f"Retrieved opponent stats for team {team_id}")
            return df

        except Exception as e:
            logger.error(f"Error fetching opponent stats for team {team_id}: {e}")
            return pd.DataFrame()

    def get_league_team_defense_stats(self) -> pd.DataFrame:
        """
        Dohvati defensive statistike za sve timove u ligi

        Returns:
            DataFrame sa defensive stats svih timova
        """
        try:
            logger.info("Fetching league defensive stats")

            def_stats = safe_api_call(
                leaguedashteamstats.LeagueDashTeamStats,
                measure_type_detailed_defense='Defense',
                season=self.season,
                timeout=self.timeout
            )

            if def_stats is None:
                return pd.DataFrame()

            df = def_stats.get_data_frames()[0]
            logger.info(f"Retrieved defensive stats for {len(df)} teams")
            return df

        except Exception as e:
            logger.error(f"Error fetching league defensive stats: {e}")
            return pd.DataFrame()

    def get_team_roster(self, team_id: int) -> pd.DataFrame:
        """
        Dohvati roster za tim

        Args:
            team_id: NBA team ID

        Returns:
            DataFrame sa roster info
        """
        try:
            logger.info(f"Fetching roster for team {team_id}")

            roster = safe_api_call(
                commonteamroster.CommonTeamRoster,
                team_id=str(team_id),
                season=self.season,
                timeout=self.timeout
            )

            if roster is None:
                return pd.DataFrame()

            df = roster.get_data_frames()[0]
            logger.info(f"Retrieved {len(df)} players in roster")
            return df

        except Exception as e:
            logger.error(f"Error fetching roster for team {team_id}: {e}")
            return pd.DataFrame()

    # ============================================================================
    # GAME DATA
    # ============================================================================

    def get_usage_stats(self, game_id: str) -> pd.DataFrame:
        """
        Dohvati usage statistike za utakmicu

        Args:
            game_id: NBA game ID

        Returns:
            DataFrame sa usage stats
        """
        try:
            logger.info(f"Fetching usage stats for game {game_id}")

            usage = safe_api_call(
                boxscoreusagev2.BoxScoreUsageV2,
                game_id=game_id,
                timeout=self.timeout
            )

            if usage is None:
                return pd.DataFrame()

            df = usage.get_data_frames()[0]
            logger.info(f"Retrieved usage stats for game {game_id}")
            return df

        except Exception as e:
            logger.error(f"Error fetching usage stats for game {game_id}: {e}")
            return pd.DataFrame()

    def find_games(self, team_id: int, vs_team_id: Optional[int] = None,
                   season: Optional[str] = None) -> pd.DataFrame:
        """
        Pronađi utakmice za tim

        Args:
            team_id: NBA team ID
            vs_team_id: Opponent team ID (optional)
            season: Season (default: current)

        Returns:
            DataFrame sa pronađenim utakmicama
        """
        try:
            logger.info(f"Finding games for team {team_id}")

            game_finder = safe_api_call(
                leaguegamefinder.LeagueGameFinder,
                team_id_nullable=str(team_id),
                vs_team_id_nullable=str(vs_team_id) if vs_team_id else None,
                season_nullable=season or self.season,
                timeout=self.timeout
            )

            if game_finder is None:
                return pd.DataFrame()

            df = game_finder.get_data_frames()[0]
            logger.info(f"Found {len(df)} games")
            return df

        except Exception as e:
            logger.error(f"Error finding games: {e}")
            return pd.DataFrame()

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def get_pace_for_team(self, team_id: int) -> float:
        """
        Dohvati pace (tempo) za tim

        Args:
            team_id: NBA team ID

        Returns:
            Pace value (possessions per game)
        """
        try:
            splits = self.get_team_splits(team_id)
            if 'overall' in splits and not splits['overall'].empty:
                df = splits['overall']
                if 'PACE' in df.columns:
                    return float(df['PACE'].iloc[0])
            return 100.0  # Default league average
        except:
            return 100.0

    def get_defensive_rating_vs_position(self, team_id: int, position: str) -> Optional[float]:
        """
        Dohvati defensive rating tima protiv specifične pozicije

        Args:
            team_id: NBA team ID
            position: 'PG', 'SG', 'SF', 'PF', 'C'

        Returns:
            Defensive rating ili None
        """
        # Napomena: NBA API nema direktan endpoint za defense by position
        # Ovo bi zahtijevalo dodatnu obradu podataka
        logger.warning("Defense by position requires custom processing")
        return None
