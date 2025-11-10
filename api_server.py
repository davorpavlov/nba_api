"""
NBA Props Analysis - Flask REST API Server
Za deployment na Coolify i integraciju sa N8N
"""

import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from analysis import DailyAnalysis, NBADataFetcher, PropsScoringModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
CORS(app)

# Configuration
CURRENT_SEASON = os.getenv('NBA_SEASON', '2025-26')
DEFAULT_MIN_CONFIDENCE = float(os.getenv('MIN_CONFIDENCE', '0.65'))
DEFAULT_TOP_N = int(os.getenv('TOP_N', '10'))

# Global instances (reuse to avoid recreating)
analysis = DailyAnalysis(season=CURRENT_SEASON)
logger.info(f"NBA Analysis API initialized for season {CURRENT_SEASON}")


# ============================================================================
# HEALTH & INFO ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint za Coolify"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'season': CURRENT_SEASON,
        'service': 'nba-props-analysis'
    }), 200


@app.route('/', methods=['GET'])
def index():
    """API info endpoint"""
    return jsonify({
        'service': 'NBA Props Analysis API',
        'version': '1.0.0',
        'season': CURRENT_SEASON,
        'endpoints': {
            'health': '/health',
            'info': '/',
            'daily_analysis': '/api/daily-analysis',
            'player_analysis': '/api/player-analysis',
            'todays_games': '/api/todays-games',
            'player_search': '/api/player-search',
            'team_search': '/api/team-search'
        },
        'documentation': 'https://github.com/davorpavlov/nba_api/tree/main/analysis'
    }), 200


# ============================================================================
# MAIN ANALYSIS ENDPOINTS
# ============================================================================

@app.route('/api/daily-analysis', methods=['GET'])
def daily_analysis():
    """
    Dnevna analiza svih utakmica

    Query params:
    - prop_types: comma-separated (default: points,rebounds,assists)
    - min_confidence: float 0-1 (default: 0.65)
    - top_n: int (default: 10)

    Example:
    GET /api/daily-analysis?prop_types=points,rebounds&min_confidence=0.70&top_n=5
    """
    try:
        # Parse query params
        prop_types_str = request.args.get('prop_types', 'points,rebounds,assists')
        prop_types = [p.strip() for p in prop_types_str.split(',')]

        min_confidence = float(request.args.get('min_confidence', DEFAULT_MIN_CONFIDENCE))
        top_n = request.args.get('top_n', DEFAULT_TOP_N)
        top_n = int(top_n) if top_n else None

        logger.info(f"Daily analysis request: prop_types={prop_types}, min_confidence={min_confidence}, top_n={top_n}")

        # Run analysis
        results = analysis.run_daily_analysis(
            prop_types=prop_types,
            min_confidence=min_confidence,
            top_n=top_n
        )

        logger.info(f"Analysis complete: {len(results)} results")

        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'params': {
                'prop_types': prop_types,
                'min_confidence': min_confidence,
                'top_n': top_n
            },
            'count': len(results),
            'results': results
        }), 200

    except Exception as e:
        logger.error(f"Error in daily analysis: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/player-analysis', methods=['GET', 'POST'])
def player_analysis():
    """
    Analiza specifičnog igrača

    GET query params:
        ?player_id=203081&prop_type=points&line=23.0

    POST body (JSON):
    {
        "player_name": "LeBron James",
        "opponent_team_name": "Golden State Warriors",
        "is_home_game": true,
        "props": {
            "points": 25.5,
            "rebounds": 7.5,
            "assists": 7.5
        }
    }
    """
    try:
        # Handle GET request with query parameters
        if request.method == 'GET':
            player_id = request.args.get('player_id')
            prop_type = request.args.get('prop_type', 'points')
            line = request.args.get('line')

            if not player_id:
                return jsonify({
                    'success': False,
                    'error': 'Missing required parameter: player_id'
                }), 400

            if not line:
                return jsonify({
                    'success': False,
                    'error': 'Missing required parameter: line'
                }), 400

            try:
                player_id = int(player_id)
                line = float(line)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid player_id or line value'
                }), 400

            logger.info(f"Quick player analysis: player_id={player_id}, {prop_type}={line}")

            # Get optional parameters
            team_id = request.args.get('team_id')
            opponent_team_id = request.args.get('opponent_team_id')
            is_home = request.args.get('is_home', 'true').lower() == 'true'

            # Get player info
            from nba_api.stats.static import players as players_static
            all_players = players_static.get_players()
            player = next((p for p in all_players if p['id'] == player_id), None)

            if not player:
                return jsonify({
                    'success': False,
                    'error': f'Player with id {player_id} not found'
                }), 404

            # If team_id not provided, try to find it from player's recent games
            if not team_id:
                try:
                    game_log = analysis.fetcher.get_player_game_log(player_id, last_n=1)
                    if not game_log.empty:
                        team_id = int(game_log.iloc[0]['TEAM_ID'])
                    else:
                        return jsonify({
                            'success': False,
                            'error': 'Could not determine player team. Please provide team_id parameter.'
                        }), 400
                except Exception as e:
                    logger.warning(f"Could not determine team_id: {e}")
                    return jsonify({
                        'success': False,
                        'error': f'Could not determine player team: {str(e)}'
                    }), 400

            # If opponent not provided, try to get today's game
            if not opponent_team_id:
                try:
                    games = analysis.fetcher.get_todays_games()
                    player_game = next((g for g in games if team_id in [g['home_team_id'], g['visitor_team_id']]), None)
                    if player_game:
                        opponent_team_id = player_game['visitor_team_id'] if team_id == player_game['home_team_id'] else player_game['home_team_id']
                        is_home = team_id == player_game['home_team_id']
                    else:
                        logger.warning(f"No game found today for team {team_id}")
                        return jsonify({
                            'success': False,
                            'error': 'No game found today for this player. Please provide opponent_team_id parameter.'
                        }), 400
                except Exception as e:
                    logger.warning(f"Could not find today's game: {e}")
                    return jsonify({
                        'success': False,
                        'error': f'Could not find today\'s game: {str(e)}'
                    }), 400

            # Now run the analysis with all required params
            result = analysis.scoring_model.analyze_player_prop(
                player_id=player_id,
                player_name=player['full_name'],
                team_id=int(team_id),
                opponent_team_id=int(opponent_team_id),
                prop_type=prop_type,
                prop_line=line,
                is_home_game=is_home
            )

            return jsonify({
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'player': player['full_name'],
                'player_id': player_id,
                'team_id': team_id,
                'opponent_team_id': opponent_team_id,
                'is_home_game': is_home,
                'prop_type': prop_type,
                'line': line,
                'result': result
            }), 200

        # Handle POST request with JSON body
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400

        # Validate required fields
        required = ['player_name', 'opponent_team_name', 'is_home_game', 'props']
        for field in required:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        logger.info(f"Player analysis request: {data['player_name']} vs {data['opponent_team_name']}")

        # Run analysis
        results = analysis.analyze_specific_player_props(
            player_name=data['player_name'],
            opponent_team_name=data['opponent_team_name'],
            is_home_game=data['is_home_game'],
            props_to_analyze=data['props']
        )

        logger.info(f"Player analysis complete: {len(results)} props analyzed")

        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'player': data['player_name'],
            'opponent': data['opponent_team_name'],
            'count': len(results),
            'results': results
        }), 200

    except Exception as e:
        logger.error(f"Error in player analysis: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@app.route('/api/todays-games', methods=['GET'])
def todays_games():
    """Dohvati sve današnje utakmice"""
    try:
        fetcher = analysis.fetcher
        games = fetcher.get_todays_games()

        logger.info(f"Found {len(games)} games today")

        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'count': len(games),
            'games': games
        }), 200

    except Exception as e:
        logger.error(f"Error fetching today's games: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/player-search', methods=['GET'])
def player_search():
    """
    Pretraži igrača po imenu

    Query params:
    - name: player name (required)

    Example:
    GET /api/player-search?name=lebron
    """
    try:
        name = request.args.get('name')

        if not name:
            return jsonify({
                'success': False,
                'error': 'Missing required parameter: name'
            }), 400

        fetcher = analysis.fetcher
        player = fetcher.get_player_by_name(name)

        if player:
            return jsonify({
                'success': True,
                'player': player
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'Player not found: {name}'
            }), 404

    except Exception as e:
        logger.error(f"Error searching player: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/team-search', methods=['GET'])
def team_search():
    """
    Pretraži tim po imenu

    Query params:
    - name: team name (required)

    Example:
    GET /api/team-search?name=lakers
    """
    try:
        name = request.args.get('name')

        if not name:
            return jsonify({
                'success': False,
                'error': 'Missing required parameter: name'
            }), 400

        fetcher = analysis.fetcher
        team = fetcher.get_team_by_name(name)

        if team:
            return jsonify({
                'success': True,
                'team': team
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'Team not found: {name}'
            }), 404

    except Exception as e:
        logger.error(f"Error searching team: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'available_endpoints': [
            '/health',
            '/',
            '/api/daily-analysis',
            '/api/player-analysis',
            '/api/todays-games',
            '/api/player-search',
            '/api/team-search'
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('DEBUG', 'False').lower() == 'true'

    logger.info(f"Starting NBA Props Analysis API on {host}:{port}")

    app.run(
        host=host,
        port=port,
        debug=debug
    )
