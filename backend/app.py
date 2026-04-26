from flask import Flask, render_template, jsonify, request
import os
import sys
from pathlib import Path
from flask_dance.contrib.google import make_google_blueprint, google
from flask import redirect, url_for
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix

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

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Flask configuration
app.secret_key = os.environ.get('SECRET_KEY', 'xcvdfgdsg')

# Google OAuth configuration (dummy values - replace with real ones)
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', 'xxxx')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', 'xxxx')

# Google OAuth blueprint
google_bp = make_google_blueprint(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    scope=["openid", 
           "https://www.googleapis.com/auth/userinfo.email",
           "https://www.googleapis.com/auth/userinfo.profile"],
    redirect_to='index'
)
app.register_blueprint(google_bp, url_prefix='/login')



#@app.route('/login')
#def login():
#    # Build the Google auth URL manually with prompt=select_account
#    google_bp.session.token = None  # clear any cached token
#    auth_url, state = google_bp.session.authorization_url(
#        "https://accounts.google.com/o/oauth2/auth",  prompt="select_account"
#    )
#    from flask import session
#    session["google_oauth_state"] = state
#    return redirect(auth_url)

@app.route('/logged-out')
def logged_out():
    return '''
        <h2>You have been logged out.</h2>
    '''

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not google.authorized:
            return redirect(url_for('google.login'))
            #return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/logout')
def logout():
    """Logout and clear OAuth session"""
    from flask import session
    # Remove the OAuth tokens explicitly
    session.pop("google_oauth_token", None)
    session.pop("facebook_oauth_token", None)
    session.modified = True
    return redirect(url_for('logged_out'))
    

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
@login_required
def index():
    """Home page - Minutes chart"""
    current_user = None
    if google.authorized:
        resp = google.get('/oauth2/v2/userinfo')
        if resp.ok:
            current_user = resp.json()
    return render_template('minutes_chart.html', current_user=current_user)


@app.route('/goals')
@login_required
def goals():
    """Goals chart page"""
    current_user = None
    if google.authorized:
        resp = google.get('/oauth2/v2/userinfo')
        if resp.ok:
            current_user = resp.json()
    return render_template('goals_chart.html', current_user=current_user)


@app.route('/efficiency')
@login_required
def efficiency():
    """Player efficiency stats page"""
    current_user = None
    if google.authorized:
        resp = google.get('/oauth2/v2/userinfo')
        if resp.ok:
            current_user = resp.json()
    return render_template('efficiency.html', current_user=current_user)


@app.route('/goal-efficiency')
@login_required
def goal_efficiency():
    """Goal efficiency per game page"""
    current_user = None
    if google.authorized:
        resp = google.get('/oauth2/v2/userinfo')
        if resp.ok:
            current_user = resp.json()
    return render_template('goal_efficiency.html', current_user=current_user)

@app.route('/games-played')
@login_required
def games_played():
    """Games played per player page"""
    current_user = None
    if google.authorized:
        resp = google.get('/oauth2/v2/userinfo')
        if resp.ok:
            current_user = resp.json()
    return render_template('games_played.html', current_user=current_user)


@app.route('/player-overview')
@login_required
def player_overview():
    """Player overview stats page"""
    current_user = None
    if google.authorized:
        resp = google.get('/oauth2/v2/userinfo')
        if resp.ok:
            current_user = resp.json()
    return render_template('player_overview.html', current_user=current_user)


@app.route('/minutes-matrix')
@login_required
def minutes_matrix():
    """Minutes matrix page"""
    current_user = None
    if google.authorized:
        resp = google.get('/oauth2/v2/userinfo')
        if resp.ok:
            current_user = resp.json()
    return render_template('minutes_matrix.html', current_user=current_user)


#
# API endpoints
#
@app.route('/api/seasons')
@login_required
def api_seasons():
    """API endpoint for available season combos"""
    data = get_all_seasons(DB_PATH)
    return jsonify(data)


@app.route('/api/minutes')
@login_required
def api_minutes():
    """API endpoint for player minutes data"""
    team, date_from, date_to = _get_filter_params()
    data = get_player_minutes(DB_PATH, team=team, date_from=date_from, date_to=date_to)
    return jsonify(data)


@app.route('/api/goals')
@login_required
def api_goals():
    """API endpoint for player goals data"""
    team, date_from, date_to = _get_filter_params()
    data = get_player_goals(DB_PATH, team=team, date_from=date_from, date_to=date_to)
    return jsonify(data)


@app.route('/api/efficiency')
@login_required
def api_efficiency():
    """API endpoint for player efficiency data"""
    team, date_from, date_to = _get_filter_params()
    data = get_player_efficiency(DB_PATH, team=team, date_from=date_from, date_to=date_to)
    return jsonify(data)


@app.route('/api/goal-efficiency')
@login_required
def api_goal_efficiency():
    """API endpoint for goal efficiency per game data"""
    team, date_from, date_to = _get_filter_params()
    data = get_goal_efficiency_per_game(DB_PATH, team=team, date_from=date_from, date_to=date_to)
    return jsonify(data)

@app.route('/api/games-played')
@login_required
def api_games_played():
    """API endpoint for games played per player"""
    team, date_from, date_to = _get_filter_params()
    data = get_games_played_per_player(DB_PATH, team=team, date_from=date_from, date_to=date_to)
    return jsonify(data)

@app.route('/api/player-overview')
@login_required
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
@login_required
def api_player_names():
    """API endpoint for all player names (for filter dropdown)"""
    team, date_from, date_to = _get_filter_params()
    data = get_all_player_names(DB_PATH, team=team, date_from=date_from, date_to=date_to)
    return jsonify(data)


@app.route('/api/minutes-matrix')
@login_required
def api_minutes_matrix():
    """API endpoint for minutes matrix (players x games)"""
    team, date_from, date_to = _get_filter_params()
    data = get_minutes_matrix(DB_PATH, team=team, date_from=date_from, date_to=date_to)
    return jsonify(data)

if __name__ == '__main__':
    # Enable debug mode with auto-reload for development
    app.run(host='0.0.0.0', port=5000, debug=True)
