import os
import sys
from datetime import timedelta
from flask import Flask, render_template, redirect, session, request, flash, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from werkzeug.middleware.proxy_fix import ProxyFix

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth import google_bp, google_auth_url, get_current_user, get_current_simple_user, login_required, admin_required
from utils.queries import authenticate_user, create_user, get_all_users, suspend_user, unsuspend_user, delete_user, change_user_password

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
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=14)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri='memory://'
)

# Cache configuration (1 hour TTL for API responses)
cache = Cache(app, config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 3600})

# Import api_bp AFTER cache is initialized
from api import api_bp, set_cache

# Inject cache into api module
set_cache(cache)

# Register blueprints
app.register_blueprint(google_bp, url_prefix='/login')  # /login/google, /login/google/authorized
app.register_blueprint(api_bp)                          # /api/*


# --- Auth routes ---

@app.route('/logout')
def logout():
    session.pop("google_oauth_token", None)
    session.pop("user_info", None)
    session.pop("simple_user", None)
    session.modified = True
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html')
        
        user = authenticate_user(username=username, password=password)
        if user:
            session.permanent = True
            session['simple_user'] = user
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
            return render_template('login.html')
    
    # Check if already logged in
    if get_current_user() or get_current_simple_user():
        return redirect(url_for('index'))
    
    return render_template('login.html')


# --- Admin routes ---

@app.route('/admin')
@admin_required
def admin():
    users = get_all_users()
    return render_template('admin.html', users=users, current_user=get_current_user())


@app.route('/admin/users', methods=['POST'])
@admin_required
def admin_users():
    action = request.form.get('action')
    user_id = request.form.get('user_id')
    
    if action == 'create':
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            admin_user = get_current_user()
            created_by = admin_user.get('email') if admin_user else 'admin'
            if create_user(username=username, password=password, created_by=created_by):
                flash('User created successfully', 'success')
            else:
                flash('Username already exists', 'error')
    
    elif action == 'suspend':
        days = request.form.get('suspend_days', type=int)
        if days and days > 0:
            import datetime
            suspended_until = (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()
            suspend_user(user_id=user_id, suspended_until=suspended_until)
            flash(f'User suspended for {days} days', 'success')
    
    elif action == 'unsuspend':
        unsuspend_user(user_id=user_id)
        flash('User unsuspended', 'success')
    
    elif action == 'delete':
        delete_user(user_id=user_id)
        flash('User deleted', 'success')
    
    elif action == 'change_password':
        new_password = request.form.get('new_password')
        if new_password:
            change_user_password(user_id=user_id, new_password=new_password)
            flash('Password changed successfully', 'success')
    
    return redirect(url_for('admin'))


# --- Page routes ---

@app.route('/')
@login_required
def index():
    return render_template('ranking.html', current_user=get_current_user(), simple_user=get_current_simple_user())


@app.route('/minutes-chart')
@login_required
def minutes_chart():
    return render_template('minutes_chart.html', current_user=get_current_user(), simple_user=get_current_simple_user())


@app.route('/goals')
@login_required
def goals():
    return render_template('goals_chart.html', current_user=get_current_user(), simple_user=get_current_simple_user())


@app.route('/efficiency')
@login_required
def efficiency():
    return render_template('efficiency.html', current_user=get_current_user(), simple_user=get_current_simple_user())


@app.route('/goal-efficiency')
@login_required
def goal_efficiency():
    return render_template('goal_efficiency.html', current_user=get_current_user(), simple_user=get_current_simple_user())


@app.route('/games-played')
@login_required
def games_played():
    return render_template('games_played.html', current_user=get_current_user(), simple_user=get_current_simple_user())


@app.route('/player-overview')
@login_required
def player_overview():
    return render_template('player_overview.html', current_user=get_current_user(), simple_user=get_current_simple_user())


@app.route('/minutes-matrix')
@login_required
def minutes_matrix():
    return render_template('minutes_matrix.html', current_user=get_current_user(), simple_user=get_current_simple_user())


@app.route('/ranking')
@login_required
def ranking():
    return render_template('ranking.html', current_user=get_current_user(), simple_user=get_current_simple_user())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
