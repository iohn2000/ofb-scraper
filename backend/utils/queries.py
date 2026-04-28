import sqlite3
from utils.db import get_connection

DEFAULT_DB = 'data/club-stats.db'


def get_all_clubs(db_path=DEFAULT_DB):
    """Return all clubs from the clubs table."""
    with get_connection(db_path) as conn:
        rows = conn.execute('SELECT id, name, short_name FROM clubs ORDER BY id ASC').fetchall()
    return [{'id': r['id'], 'name': r['name'], 'short_name': r['short_name']} for r in rows]


def get_all_seasons(db_path=DEFAULT_DB):
    """Return all valid season combos from the seasons table."""
    with get_connection(db_path) as conn:
        rows = conn.execute('''
            SELECT age_group, season_year, date_from, date_to
            FROM seasons
            ORDER BY season_year DESC, age_group ASC
        ''').fetchall()
    return [dict(r) for r in rows]


def get_season_dates(db_path, team, year):
    """Look up date_from and date_to for a given team + year."""
    with get_connection(db_path) as conn:
        row = conn.execute('''
            SELECT date_from, date_to FROM seasons
            WHERE age_group = ? AND season_year = ?
        ''', (team, year)).fetchone()
    if row:
        return row['date_from'], row['date_to']
    return None, None


def get_player_minutes(db_path=DEFAULT_DB, team="U13", date_from='2025-08-29', date_to='2026-06-08', club_id=1):
    """Get total minutes played per player."""
    with get_connection(db_path) as conn:
        rows = conn.execute('''
            SELECT p.player_name, SUM(g.minutes_played) as total_minutes
            FROM players p
            JOIN games g ON p.player_id = g.player_id AND g.club_id = p.club_id
            WHERE g.game_date BETWEEN ? AND ?
                AND g.age_group = ? AND p.team = ?
                AND p.club_id = ? AND g.club_id = ?
            GROUP BY p.player_id, p.player_name
            ORDER BY total_minutes DESC
        ''', (date_from, date_to, team, team, club_id, club_id)).fetchall()
    return {
        'labels': [r['player_name'] for r in rows],
        'data': [r['total_minutes'] or 0 for r in rows]
    }


def get_player_goals(db_path=DEFAULT_DB, team="U13", date_from='2025-08-29', date_to='2026-06-08', club_id=1):
    """Get total goals scored per player."""
    with get_connection(db_path) as conn:
        rows = conn.execute('''
            SELECT p.player_name, SUM(g.goals) as total_goals
            FROM players p
            JOIN games g ON p.player_id = g.player_id AND g.club_id = p.club_id
            WHERE g.game_date BETWEEN ? AND ?
                AND g.age_group = ? AND p.team = ?
                AND p.club_id = ? AND g.club_id = ?
            GROUP BY p.player_id, p.player_name
            HAVING SUM(g.goals) > 0
            ORDER BY total_goals DESC
        ''', (date_from, date_to, team, team, club_id, club_id)).fetchall()
    return {
        'labels': [r['player_name'] for r in rows],
        'data': [r['total_goals'] or 0 for r in rows]
    }


def get_player_efficiency(db_path=DEFAULT_DB, team="U13", date_from='2025-08-29', date_to='2026-06-08', club_id=1):
    """Get player efficiency stats aggregated across all games."""
    with get_connection(db_path) as conn:
        rows = conn.execute('''
            SELECT
                p.player_name,
                COUNT(DISTINCT g.id) as total_games,
                SUM(g.goals) as total_goals,
                SUM(g.minutes_played) as total_minutes,
                ROUND(CAST(SUM(g.goals) AS FLOAT) / SUM(g.minutes_played) * 90, 3) as goals_per_90_minutes,
                ROUND(CAST(SUM(g.minutes_played) AS FLOAT) / SUM(g.goals), 2) as minutes_per_goal,
                ROUND(CAST(SUM(g.goals) AS FLOAT) / COUNT(DISTINCT g.id), 2) as goals_per_game
            FROM games g
            JOIN players p ON g.player_id = p.player_id AND g.club_id = p.club_id
            WHERE g.game_date BETWEEN ? AND ?
                AND g.age_group = ? AND g.club_id = ?
                AND (g.goals > 0 OR g.minutes_played > 0)
            GROUP BY p.player_id, p.player_name
            HAVING SUM(g.goals) > 0 AND SUM(g.minutes_played) > 0
            ORDER BY goals_per_90_minutes DESC, minutes_per_goal ASC
        ''', (date_from, date_to, team, club_id)).fetchall()
    return [dict(r) for r in rows]


def get_minutes_matrix(db_path=DEFAULT_DB, team="U13", date_from='2025-08-29', date_to='2026-06-08', club_id=1):
    """Returns a matrix of all games (x-axis) and all players (y-axis), with minutes played per cell."""
    with get_connection(db_path) as conn:
        games = conn.execute('''
            SELECT MIN(id) as id, game_date, competition, home_team, away_team
            FROM games
            WHERE game_date BETWEEN ? AND ? AND age_group = ? AND club_id = ?
            GROUP BY game_date, competition, home_team, away_team
            ORDER BY game_date ASC, id ASC
        ''', (date_from, date_to, team, club_id)).fetchall()

        players = conn.execute('''
            SELECT player_id, player_name FROM players
            WHERE team = ? AND club_id = ? AND season_year = (
                SELECT season_year FROM seasons WHERE age_group = ? AND date_from = ? LIMIT 1
            )
            ORDER BY player_name ASC
        ''', (team, club_id, team, date_from)).fetchall()

        # Fetch all minutes in one query instead of N*M individual queries
        all_minutes = conn.execute('''
            SELECT player_id, game_date, competition, home_team, away_team,
                   SUM(minutes_played) as mins
            FROM games
            WHERE game_date BETWEEN ? AND ? AND age_group = ? AND club_id = ?
            GROUP BY player_id, game_date, competition, home_team, away_team
        ''', (date_from, date_to, team, club_id)).fetchall()

        # Fetch results per game in one query
        game_results = conn.execute('''
            SELECT game_date, competition, home_team, away_team,
                   result, COUNT(*) as cnt
            FROM games
            WHERE game_date BETWEEN ? AND ? AND age_group = ? AND club_id = ?
            GROUP BY game_date, competition, home_team, away_team, result
            ORDER BY cnt DESC
        ''', (date_from, date_to, team, club_id)).fetchall()

    # Build minutes lookup: (player_id, game_date, comp, home, away) -> minutes
    minutes_lookup = {}
    for row in all_minutes:
        key = (row['player_id'], row['game_date'], row['competition'], row['home_team'], row['away_team'])
        minutes_lookup[key] = row['mins'] or 0

    # Build result lookup: (game_date, comp, home, away) -> result (most common)
    result_lookup = {}
    for row in game_results:
        key = (row['game_date'], row['competition'], row['home_team'], row['away_team'])
        if key not in result_lookup:
            result_lookup[key] = row['result'] or ''

    # Build matrix
    matrix = {}
    for p in players:
        pid = p['player_id']
        matrix[pid] = {}
        for g in games:
            key = (pid, g['game_date'], g['competition'], g['home_team'], g['away_team'])
            matrix[pid][g['id']] = minutes_lookup.get(key, 0)

    players_obj = [{'id': p['player_id'], 'name': p['player_name']} for p in players]
    games_obj = []
    for g in games:
        rkey = (g['game_date'], g['competition'], g['home_team'], g['away_team'])
        games_obj.append({
            'id': g['id'], 'date': g['game_date'], 'competition': g['competition'],
            'home_team': g['home_team'], 'away_team': g['away_team'],
            'result': result_lookup.get(rkey, '')
        })

    return {'games': games_obj, 'players': players_obj, 'matrix': matrix}


def get_goal_efficiency_per_game(db_path=DEFAULT_DB, team="U13", date_from='2025-08-29', date_to='2026-06-08', club_id=1):
    """Get goal efficiency per individual game, sorted by best efficiency first."""
    with get_connection(db_path) as conn:
        rows = conn.execute('''
            SELECT
                p.player_name, g.game_date, g.competition,
                g.home_team, g.away_team, g.goals, g.minutes_played,
                ROUND(CAST(g.goals AS FLOAT) / g.minutes_played * 90, 3) as goals_per_90_minutes,
                ROUND(CAST(g.minutes_played AS FLOAT) / g.goals, 2) as minutes_per_goal
            FROM games g
            JOIN players p ON g.player_id = p.player_id AND g.club_id = p.club_id
            WHERE g.game_date BETWEEN ? AND ?
                AND g.age_group = ? AND g.club_id = ?
                AND g.goals > 0 AND g.minutes_played > 0
            ORDER BY goals_per_90_minutes DESC, minutes_per_goal ASC, g.game_date DESC
        ''', (date_from, date_to, team, club_id)).fetchall()
    return [dict(r) for r in rows]


def get_player_overview(db_path=DEFAULT_DB, team="U13", date_from='2025-08-29', date_to='2026-06-08',
                       players=None, sort_by='player_name', sort_dir='asc', club_id=1):
    """Get per-player overview: games, minutes, goals, avg minutes/game, avg goals/game."""
    VALID_SORT_COLS = {
        'player_name': 'p.player_name',
        'games_played': 'games_played',
        'total_minutes': 'total_minutes',
        'total_goals': 'total_goals',
        'avg_minutes_per_game': 'avg_minutes_per_game',
        'avg_goals_per_game': 'avg_goals_per_game',
    }
    sort_col = VALID_SORT_COLS.get(sort_by, 'p.player_name')
    sort_direction = 'DESC' if sort_dir.lower() == 'desc' else 'ASC'

    base_query = '''
        SELECT
            p.player_name,
            COUNT(*) AS games_played,
            SUM(g.minutes_played) AS total_minutes,
            COALESCE(SUM(g.goals), 0) AS total_goals,
            ROUND(CAST(SUM(g.minutes_played) AS FLOAT) / COUNT(*), 1) AS avg_minutes_per_game,
            ROUND(CAST(COALESCE(SUM(g.goals), 0) AS FLOAT) / COUNT(*), 2) AS avg_goals_per_game
        FROM players p
        JOIN games g ON p.player_id = g.player_id AND g.club_id = p.club_id
        WHERE g.game_date BETWEEN ? AND ?
            AND g.age_group = ? AND p.team = ?
            AND p.club_id = ? AND g.club_id = ?
            AND g.minutes_played > 0
    '''
    params = [date_from, date_to, team, team, club_id, club_id]

    if players:
        placeholders = ','.join('?' for _ in players)
        base_query += f' AND p.player_name IN ({placeholders})'
        params.extend(players)

    base_query += f'''
        GROUP BY p.player_id, p.player_name
        ORDER BY {sort_col} {sort_direction}
    '''

    with get_connection(db_path) as conn:
        rows = conn.execute(base_query, params).fetchall()
    return [
        {
            'player_name': r['player_name'],
            'games_played': r['games_played'],
            'total_minutes': r['total_minutes'] or 0,
            'total_goals': r['total_goals'] or 0,
            'avg_minutes_per_game': r['avg_minutes_per_game'] or 0,
            'avg_goals_per_game': r['avg_goals_per_game'] or 0,
        }
        for r in rows
    ]


def get_all_player_names(db_path=DEFAULT_DB, team="U13", date_from='2025-08-29', date_to='2026-06-08', club_id=1):
    """Return sorted list of player names that have game data in the given season."""
    with get_connection(db_path) as conn:
        rows = conn.execute('''
            SELECT DISTINCT p.player_name
            FROM players p
            JOIN games g ON p.player_id = g.player_id AND g.club_id = p.club_id
            WHERE g.game_date BETWEEN ? AND ?
                AND g.age_group = ? AND p.team = ?
                AND p.club_id = ? AND g.club_id = ?
                AND g.minutes_played > 0
            ORDER BY p.player_name ASC
        ''', (date_from, date_to, team, team, club_id, club_id)).fetchall()
    return [r['player_name'] for r in rows]


def get_games_played_per_player(db_path=DEFAULT_DB, team="U13", date_from='2025-08-29', date_to='2026-06-08', club_id=1):
    """Get the number of games played per player."""
    with get_connection(db_path) as conn:
        rows = conn.execute('''
            SELECT p.player_name, COUNT(*) AS num_games
            FROM players p
            JOIN games g ON p.player_id = g.player_id AND g.club_id = p.club_id
            WHERE g.game_date BETWEEN ? AND ?
                AND g.age_group = ? AND p.team = ?
                AND p.club_id = ? AND g.club_id = ?
                AND g.minutes_played > 0
            GROUP BY p.player_id, p.player_name
            ORDER BY num_games DESC
        ''', (date_from, date_to, team, team, club_id, club_id)).fetchall()
    return [dict(r) for r in rows]
