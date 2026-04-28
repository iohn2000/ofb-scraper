import os
from flask import Blueprint, jsonify, request
from auth import login_required
from utils.queries import (
    get_games_played_per_player, get_player_minutes, get_player_goals,
    get_player_efficiency, get_goal_efficiency_per_game, get_minutes_matrix,
    get_all_seasons, get_season_dates, get_player_overview, get_all_player_names
)

api_bp = Blueprint('api', __name__)

DB_PATH = '/app/ofb_stats.db'
if not os.path.exists(DB_PATH):
    DB_PATH = 'ofb_stats.db'


def _get_filter_params():
    """Extract team/year from query string and look up season date range."""
    team = request.args.get('team', 'U13')
    year = request.args.get('year', 2026, type=int)
    date_from, date_to = get_season_dates(DB_PATH, team, year)
    if date_from is None:
        date_from = f'{year - 1}-08-29'
        date_to = f'{year}-06-08'
    return team, date_from, date_to


@api_bp.route('/api/seasons')
@login_required
def api_seasons():
    return jsonify(get_all_seasons(DB_PATH))


@api_bp.route('/api/minutes')
@login_required
def api_minutes():
    team, date_from, date_to = _get_filter_params()
    return jsonify(get_player_minutes(DB_PATH, team=team, date_from=date_from, date_to=date_to))


@api_bp.route('/api/goals')
@login_required
def api_goals():
    team, date_from, date_to = _get_filter_params()
    return jsonify(get_player_goals(DB_PATH, team=team, date_from=date_from, date_to=date_to))


@api_bp.route('/api/efficiency')
@login_required
def api_efficiency():
    team, date_from, date_to = _get_filter_params()
    return jsonify(get_player_efficiency(DB_PATH, team=team, date_from=date_from, date_to=date_to))


@api_bp.route('/api/goal-efficiency')
@login_required
def api_goal_efficiency():
    team, date_from, date_to = _get_filter_params()
    return jsonify(get_goal_efficiency_per_game(DB_PATH, team=team, date_from=date_from, date_to=date_to))


@api_bp.route('/api/games-played')
@login_required
def api_games_played():
    team, date_from, date_to = _get_filter_params()
    return jsonify(get_games_played_per_player(DB_PATH, team=team, date_from=date_from, date_to=date_to))


@api_bp.route('/api/player-overview')
@login_required
def api_player_overview():
    team, date_from, date_to = _get_filter_params()
    players_param = request.args.get('players', '')
    players = [p.strip() for p in players_param.split(',') if p.strip()] if players_param else None
    sort_by = request.args.get('sort_by', 'player_name')
    sort_dir = request.args.get('sort_dir', 'asc')
    return jsonify(get_player_overview(
        DB_PATH, team=team, date_from=date_from, date_to=date_to,
        players=players, sort_by=sort_by, sort_dir=sort_dir
    ))


@api_bp.route('/api/player-names')
@login_required
def api_player_names():
    team, date_from, date_to = _get_filter_params()
    return jsonify(get_all_player_names(DB_PATH, team=team, date_from=date_from, date_to=date_to))


@api_bp.route('/api/minutes-matrix')
@login_required
def api_minutes_matrix():
    team, date_from, date_to = _get_filter_params()
    return jsonify(get_minutes_matrix(DB_PATH, team=team, date_from=date_from, date_to=date_to))
