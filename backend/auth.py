import os
from functools import wraps
from flask import redirect, session, url_for
from flask_dance.contrib.google import make_google_blueprint, google

# Allowed emails - set ALLOWED_EMAILS=a@gmail.com,b@gmail.com in environment
ALLOWED_EMAILS = set(
    e.strip() for e in os.environ.get('ALLOWED_EMAILS', '').split(',') if e.strip()
)

# Google OAuth blueprint - registered in app.py
google_bp = make_google_blueprint(
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ],
    redirect_to='index'
)


def google_auth_url(prompt="select_account"):
    """Build a Google auth URL with prompt parameter."""
    google_bp.session.redirect_uri = url_for('google.authorized', _external=True)
    auth_url, state = google_bp.session.authorization_url(
        "https://accounts.google.com/o/oauth2/auth",
        prompt=prompt  # only prompt here, redirect_uri set on session above
    )
    session["google_oauth_state"] = state
    return auth_url


def get_current_user():
    """Return user info dict, cached in session to avoid repeated Google API calls."""
    if not google.authorized:
        return None
    if 'user_info' not in session:
        resp = google.get('/oauth2/v2/userinfo')
        if resp.ok:
            session['user_info'] = resp.json()
    return session.get('user_info')


def login_required(f):
    """Decorator that blocks unauthenticated users and enforces the email whitelist."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not google.authorized:
            return redirect(google_auth_url())
        if ALLOWED_EMAILS:
            user = get_current_user()
            if not user or user.get('email') not in ALLOWED_EMAILS:
                session.pop("google_oauth_token", None)
                session.pop("user_info", None)
                return "Access denied", 403
        return f(*args, **kwargs)
    return decorated_function
