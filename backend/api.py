import os
from flask import Blueprint, jsonify, request
from auth import login_required
from utils.queries import (
    get_games_played_per_player, get_player_minutes,
    get_player_efficiency, get_goal_efficiency_per_game, get_minutes_matrix,
    get_all_seasons, get_season_dates, get_player_overview, get_all_player_names,
    get_all_clubs, get_player_goals_breakdown
)
from utils.ranking_fetcher import get_ranking

api_bp = Blueprint('api', __name__)

# Cache instance (will be injected by app.py)
cache = None

def set_cache(cache_instance):
    """Inject cache instance from app.py"""
    global cache
    cache = cache_instance

DB_PATH = '/app/club-stats.db'
if not os.path.exists(DB_PATH):
    DB_PATH = 'data/club-stats.db'


def _get_filter_params():
    """Extract club/team/year from query string and look up season date range."""
    club_id = request.args.get('club', 1, type=int)
    team = request.args.get('team', 'U13')
    year = request.args.get('year', 2026, type=int)
    date_from, date_to = get_season_dates(DB_PATH, team, year)
    if date_from is None:
        date_from = f'{year - 1}-08-29'
        date_to = f'{year}-06-08'
    return club_id, team, date_from, date_to


@api_bp.route('/api/clubs')
@login_required
def api_clubs():
    if cache:
        cached_result = cache.get('api_clubs')
        if cached_result:
            return cached_result
    result = jsonify(get_all_clubs(DB_PATH))
    if cache:
        cache.set('api_clubs', result, timeout=3600)
    return result


@api_bp.route('/api/seasons')
@login_required
def api_seasons():
    if cache:
        cached_result = cache.get('api_seasons')
        if cached_result:
            return cached_result
    result = jsonify(get_all_seasons(DB_PATH))
    if cache:
        cache.set('api_seasons', result, timeout=3600)
    return result


@api_bp.route('/api/minutes')
@login_required
def api_minutes():
    club_id, team, date_from, date_to = _get_filter_params()
    location = request.args.get('location', None)
    half = request.args.get('half', None)
    cache_key = f"api_minutes_{club_id}_{team}_{date_from}_{date_to}_{location}_{half}"
    if cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
    result = jsonify(get_player_minutes(DB_PATH, team=team, date_from=date_from, date_to=date_to, club_id=club_id, location=location, half=half))
    if cache:
        cache.set(cache_key, result, timeout=3600)
    return result


@api_bp.route('/api/goals/breakdown')
@login_required
def api_goals_breakdown():
    club_id, team, date_from, date_to = _get_filter_params()
    location = request.args.get('location', None)
    half = request.args.get('half', None)
    cache_key = f"api_goals_breakdown_{club_id}_{team}_{date_from}_{date_to}_{location}_{half}"
    if cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
    result = jsonify(get_player_goals_breakdown(
        DB_PATH, team=team, date_from=date_from, date_to=date_to, 
        club_id=club_id, location=location, half=half
    ))
    if cache:
        cache.set(cache_key, result, timeout=3600)
    return result


@api_bp.route('/api/efficiency')
@login_required
def api_efficiency():
    club_id, team, date_from, date_to = _get_filter_params()
    cache_key = f"api_efficiency_{club_id}_{team}_{date_from}_{date_to}"
    if cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
    result = jsonify(get_player_efficiency(DB_PATH, team=team, date_from=date_from, date_to=date_to, club_id=club_id))
    if cache:
        cache.set(cache_key, result, timeout=3600)
    return result


@api_bp.route('/api/goal-efficiency')
@login_required
def api_goal_efficiency():
    club_id, team, date_from, date_to = _get_filter_params()
    cache_key = f"api_goal_efficiency_{club_id}_{team}_{date_from}_{date_to}"
    if cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
    result = jsonify(get_goal_efficiency_per_game(DB_PATH, team=team, date_from=date_from, date_to=date_to, club_id=club_id))
    if cache:
        cache.set(cache_key, result, timeout=3600)
    return result


@api_bp.route('/api/games-played')
@login_required
def api_games_played():
    club_id, team, date_from, date_to = _get_filter_params()
    location = request.args.get('location', None)
    half = request.args.get('half', None)
    cache_key = f"api_games_played_{club_id}_{team}_{date_from}_{date_to}_{location}_{half}"
    if cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
    result = jsonify(get_games_played_per_player(DB_PATH, team=team, date_from=date_from, date_to=date_to, club_id=club_id, location=location, half=half))
    if cache:
        cache.set(cache_key, result, timeout=3600)
    return result


@api_bp.route('/api/player-overview')
@login_required
def api_player_overview():
    club_id, team, date_from, date_to = _get_filter_params()
    players_param = request.args.get('players', '')
    players = [p.strip() for p in players_param.split(',') if p.strip()] if players_param else None
    sort_by = request.args.get('sort_by', 'player_name')
    sort_dir = request.args.get('sort_dir', 'asc')
    cache_key = f"api_player_overview_{club_id}_{team}_{date_from}_{date_to}_{players_param}_{sort_by}_{sort_dir}"
    if cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
    result = jsonify(get_player_overview(
        DB_PATH, team=team, date_from=date_from, date_to=date_to,
        players=players, sort_by=sort_by, sort_dir=sort_dir, club_id=club_id
    ))
    if cache:
        cache.set(cache_key, result, timeout=3600)
    return result


@api_bp.route('/api/player-names')
@login_required
def api_player_names():
    club_id, team, date_from, date_to = _get_filter_params()
    cache_key = f"api_player_names_{club_id}_{team}_{date_from}_{date_to}"
    if cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
    result = jsonify(get_all_player_names(DB_PATH, team=team, date_from=date_from, date_to=date_to, club_id=club_id))
    if cache:
        cache.set(cache_key, result, timeout=3600)
    return result


@api_bp.route('/api/minutes-matrix')
@login_required
def api_minutes_matrix():
    club_id, team, date_from, date_to = _get_filter_params()
    cache_key = f"api_minutes_matrix_{club_id}_{team}_{date_from}_{date_to}"
    if cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
    result = jsonify(get_minutes_matrix(DB_PATH, team=team, date_from=date_from, date_to=date_to, club_id=club_id))
    if cache:
        cache.set(cache_key, result, timeout=3600)
    return result


@api_bp.route('/api/ranking')
@login_required
def api_ranking():
    """Fetch B-Liga ranking for specified team and table type."""
    team = request.args.get('team', 'U13')
    table_type = request.args.get('table_type', 'NORMAL')
    cache_key = f"api_ranking_{team}_{table_type}"
    if cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
    result = jsonify(get_ranking(team=team, table_type=table_type))
    if cache:
        cache.set(cache_key, result, timeout=3600)
    return result
