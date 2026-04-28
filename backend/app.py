import os
import sys
from flask import Flask, render_template, redirect, session
from werkzeug.middleware.proxy_fix import ProxyFix

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth import google_bp, google_auth_url, get_current_user, login_required
from api import api_bp

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Flask configuration
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise RuntimeError("SECRET_KEY environment variable is not set")

if not os.environ.get('GOOGLE_CLIENT_ID') or not os.environ.get('GOOGLE_CLIENT_SECRET'):
    raise RuntimeError("Missing Google OAuth credentials in environment")

# Session cookie security
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Register blueprints
app.register_blueprint(google_bp, url_prefix='/login')  # /login/google, /login/google/authorized
app.register_blueprint(api_bp)                          # /api/*


# --- Auth routes ---

@app.route('/logout')
def logout():
    session.pop("google_oauth_token", None)
    session.pop("user_info", None)
    session.modified = True
    return redirect(google_auth_url())


# --- Page routes ---

@app.route('/')
@login_required
def index():
    return render_template('minutes_chart.html', current_user=get_current_user())


@app.route('/goals')
@login_required
def goals():
    return render_template('goals_chart.html', current_user=get_current_user())


@app.route('/efficiency')
@login_required
def efficiency():
    return render_template('efficiency.html', current_user=get_current_user())


@app.route('/goal-efficiency')
@login_required
def goal_efficiency():
    return render_template('goal_efficiency.html', current_user=get_current_user())


@app.route('/games-played')
@login_required
def games_played():
    return render_template('games_played.html', current_user=get_current_user())


@app.route('/player-overview')
@login_required
def player_overview():
    return render_template('player_overview.html', current_user=get_current_user())


@app.route('/minutes-matrix')
@login_required
def minutes_matrix():
    return render_template('minutes_matrix.html', current_user=get_current_user())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
