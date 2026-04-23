from flask import Flask, render_template, jsonify, request
import os
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.queries import (
    get_games_played_per_player, get_player_minutes, get_player_goals,
    get_player_efficiency, get_goal_efficiency_per_game, get_minutes_matrix,
    get_all_seasons, get_season_dates, get_player_overview, get_all_player_names
)

app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

# Database path
DB_PATH = '/app/ofb_stats.db'
if not os.path.exists(DB_PATH):
    # Fallback for local development
    DB_PATH = 'ofb_stats.db'


def _get_filter_params():
    """Extract team/year from query string and look up season date range."""
    team = request.args.get('team', 'U13')
    year = request.args.get('year', 2026, type=int)
    date_from, date_to = get_season_dates(DB_PATH, team, year)
    if date_from is None:
        # Fallback defaults
        date_from = f'{year - 1}-08-29'
        date_to = f'{year}-06-08'
    return team, date_from, date_to


@app.route('/')
def index():
    """Home page - Minutes chart"""
    return render_template('minutes_chart.html')


@app.route('/goals')
def goals():
    """Goals chart page"""
    return render_template('goals_chart.html')


@app.route('/efficiency')
def efficiency():
    """Player efficiency stats page"""
    return render_template('efficiency.html')


@app.route('/goal-efficiency')
def goal_efficiency():
    """Goal efficiency per game page"""
    return render_template('goal_efficiency.html')

@app.route('/games-played')
def games_played():
    """Games played per player page"""
    return render_template('games_played.html')


@app.route('/player-overview')
def player_overview():
    """Player overview stats page"""
    return render_template('player_overview.html')


@app.route('/minutes-matrix')
def minutes_matrix():
    """Minutes matrix page"""
    return render_template('minutes_matrix.html')


#
# API endpoints
#
@app.route('/api/seasons')
def api_seasons():
    """API endpoint for available season combos"""
    data = get_all_seasons(DB_PATH)
    return jsonify(data)


@app.route('/api/minutes')
def api_minutes():
    """API endpoint for player minutes data"""
    team, date_from, date_to = _get_filter_params()
    data = get_player_minutes(DB_PATH, team=team, date_from=date_from, date_to=date_to)
    return jsonify(data)


@app.route('/api/goals')
def api_goals():
    """API endpoint for player goals data"""
    team, date_from, date_to = _get_filter_params()
    data = get_player_goals(DB_PATH, team=team, date_from=date_from, date_to=date_to)
    return jsonify(data)


@app.route('/api/efficiency')
def api_efficiency():
    """API endpoint for player efficiency data"""
    team, date_from, date_to = _get_filter_params()
    data = get_player_efficiency(DB_PATH, team=team, date_from=date_from, date_to=date_to)
    return jsonify(data)


@app.route('/api/goal-efficiency')
def api_goal_efficiency():
    """API endpoint for goal efficiency per game data"""
    team, date_from, date_to = _get_filter_params()
    data = get_goal_efficiency_per_game(DB_PATH, team=team, date_from=date_from, date_to=date_to)
    return jsonify(data)

@app.route('/api/games-played')
def api_games_played():
    """API endpoint for games played per player"""
    team, date_from, date_to = _get_filter_params()
    data = get_games_played_per_player(DB_PATH, team=team, date_from=date_from, date_to=date_to)
    return jsonify(data)

@app.route('/api/player-overview')
def api_player_overview():
    """API endpoint for player overview data with server-side sorting and filtering"""
    team, date_from, date_to = _get_filter_params()
    players_param = request.args.get('players', '')
    players = [p.strip() for p in players_param.split(',') if p.strip()] if players_param else None
    sort_by = request.args.get('sort_by', 'player_name')
    sort_dir = request.args.get('sort_dir', 'asc')
    data = get_player_overview(DB_PATH, team=team, date_from=date_from, date_to=date_to,
                               players=players, sort_by=sort_by, sort_dir=sort_dir)
    return jsonify(data)


@app.route('/api/player-names')
def api_player_names():
    """API endpoint for all player names (for filter dropdown)"""
    team, date_from, date_to = _get_filter_params()
    data = get_all_player_names(DB_PATH, team=team, date_from=date_from, date_to=date_to)
    return jsonify(data)


@app.route('/api/minutes-matrix')
def api_minutes_matrix():
    """API endpoint for minutes matrix (players x games)"""
    team, date_from, date_to = _get_filter_params()
    data = get_minutes_matrix(DB_PATH, team=team, date_from=date_from, date_to=date_to)
    return jsonify(data)

if __name__ == '__main__':
    # Enable debug mode with auto-reload for development
    app.run(host='0.0.0.0', port=5000, debug=True)
