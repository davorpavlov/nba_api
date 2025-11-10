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
CURRENT_SEASON = os.getenv('NBA_SEASON', '2024-25')
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


@app.route('/api/player-analysis', methods=['POST'])
def player_analysis():
    """
    Analiza specifičnog igrača

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
