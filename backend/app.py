from flask import Flask, render_template, jsonify
import os
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.queries import get_player_minutes, get_player_goals, get_player_efficiency, get_goal_efficiency_per_game

app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

# Database path
DB_PATH = '/app/ofb_stats.db'
if not os.path.exists(DB_PATH):
    # Fallback for local development
    DB_PATH = 'ofb_stats.db'


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


@app.route('/api/minutes')
def api_minutes():
    """API endpoint for player minutes data"""
    data = get_player_minutes(DB_PATH)
    return jsonify(data)


@app.route('/api/goals')
def api_goals():
    """API endpoint for player goals data"""
    data = get_player_goals(DB_PATH)
    return jsonify(data)


@app.route('/api/efficiency')
def api_efficiency():
    """API endpoint for player efficiency data"""
    data = get_player_efficiency(DB_PATH)
    return jsonify(data)


@app.route('/api/goal-efficiency')
def api_goal_efficiency():
    """API endpoint for goal efficiency per game data"""
    data = get_goal_efficiency_per_game(DB_PATH)
    return jsonify(data)


if __name__ == '__main__':
    # Enable debug mode with auto-reload for development
    app.run(host='0.0.0.0', port=5000, debug=True)
