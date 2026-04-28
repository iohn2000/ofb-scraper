import sqlite3
from datetime import datetime


def get_all_clubs(db_path='data/club-stats.db'):
    """Return all clubs from the clubs table."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, short_name FROM clubs ORDER BY id ASC')
        results = cursor.fetchall()
        conn.close()
        return [{'id': r[0], 'name': r[1], 'short_name': r[2]} for r in results]
    except Exception as e:
        print(f"Error fetching clubs: {e}")
        return []


def get_all_seasons(db_path='data/club-stats.db'):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT age_group, season_year, date_from, date_to
            FROM seasons
            ORDER BY season_year DESC, age_group ASC
        ''')
        results = cursor.fetchall()
        conn.close()
        return [
            {'age_group': r[0], 'season_year': r[1], 'date_from': r[2], 'date_to': r[3]}
            for r in results
        ]
    except Exception as e:
        print(f"Error fetching seasons: {e}")
        return []


def get_season_dates(db_path, team, year):
    """Look up date_from and date_to for a given team + year."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT date_from, date_to FROM seasons
            WHERE age_group = ? AND season_year = ?
        ''', (team, year))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0], row[1]
        return None, None
    except Exception as e:
        print(f"Error fetching season dates: {e}")
        return None, None


def get_player_minutes(db_path='data/club-stats.db', team="U13", date_from='2025-08-29', date_to='2026-06-08', club_id=1):
    """Get total minutes played per player."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                p.player_name,
                SUM(g.minutes_played) as total_minutes
            FROM players p
            LEFT JOIN games g ON p.player_id = g.player_id AND g.club_id = p.club_id
            WHERE 
                g.game_date BETWEEN ? AND ?
                AND g.age_group = ? AND p.team = ?
                AND p.club_id = ? AND g.club_id = ?
            GROUP BY p.player_id, p.player_name
            ORDER BY total_minutes DESC
        ''', (date_from, date_to, team, team, club_id, club_id))
        results = cursor.fetchall()
        conn.close()
        player_names = [row[0] for row in results]
        total_minutes = [row[1] if row[1] else 0 for row in results]
        return {'labels': player_names, 'data': total_minutes}
    except Exception as e:
        print(f"Error fetching minutes data: {e}")
        return {'labels': [], 'data': []}


def get_player_goals(db_path='data/club-stats.db', team="U13", date_from='2025-08-29', date_to='2026-06-08', club_id=1):
    """Get total goals scored per player."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                p.player_name,
                SUM(g.goals) as total_goals
            FROM players p
            LEFT JOIN games g ON p.player_id = g.player_id AND g.club_id = p.club_id
            WHERE 
                g.game_date BETWEEN ? AND ?
                AND g.age_group = ? AND p.team = ?
                AND p.club_id = ? AND g.club_id = ?
            GROUP BY p.player_id, p.player_name
            HAVING SUM(g.goals) > 0
            ORDER BY total_goals DESC
        ''', (date_from, date_to, team, team, club_id, club_id))
        results = cursor.fetchall()
        conn.close()
        player_names = [row[0] for row in results]
        total_goals = [row[1] if row[1] else 0 for row in results]
        return {'labels': player_names, 'data': total_goals}
    except Exception as e:
        print(f"Error fetching goals data: {e}")
        return {'labels': [], 'data': []}


def get_player_efficiency(db_path='data/club-stats.db', team="U13", date_from='2025-08-29', date_to='2026-06-08', club_id=1):
    """Get player efficiency stats aggregated across all games."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                p.player_name,
                COUNT(DISTINCT g.id) as total_games,
                SUM(g.goals) as total_goals,
                SUM(g.minutes_played) as total_minutes,
                ROUND(CAST(SUM(g.goals) AS FLOAT) / SUM(g.minutes_played) * 90, 3) as goals_per_90_minutes,
                ROUND(CAST(SUM(g.minutes_played) AS FLOAT) / SUM(g.goals), 2) as minutes_per_goal,
                ROUND(CAST(SUM(g.goals) AS FLOAT) / COUNT(DISTINCT g.id), 2) as goals_per_game
            FROM 
                games g
                JOIN players p ON g.player_id = p.player_id AND g.club_id = p.club_id
            WHERE 
                g.game_date BETWEEN ? AND ?
                AND g.age_group = ?
                AND g.club_id = ?
                AND (g.goals > 0 OR g.minutes_played > 0)
            GROUP BY 
                p.player_id, p.player_name
            HAVING 
                SUM(g.goals) > 0
                AND SUM(g.minutes_played) > 0
            ORDER BY 
                goals_per_90_minutes DESC,
                minutes_per_goal ASC
        ''', (date_from, date_to, team, club_id))
        results = cursor.fetchall()
        conn.close()
        players = []
        for row in results:
            players.append({
                'player_name': row[0],
                'total_games': row[1],
                'total_goals': row[2],
                'total_minutes': row[3],
                'goals_per_90_minutes': row[4],
                'minutes_per_goal': row[5],
                'goals_per_game': row[6]
            })
        return players
    except Exception as e:
        print(f"Error fetching efficiency data: {e}")
        return []


def get_minutes_matrix(db_path='data/club-stats.db', team="U13", date_from='2025-08-29', date_to='2026-06-08', club_id=1):
    """
    Returns a matrix of all games (x-axis) and all players (y-axis),
    with each cell showing the minutes played.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT MIN(id) as id, game_date, competition, home_team, away_team
            FROM games
            WHERE game_date BETWEEN ? AND ?
                AND age_group = ?
                AND club_id = ?
            GROUP BY game_date, competition, home_team, away_team
            ORDER BY game_date ASC, id ASC
        ''', (date_from, date_to, team, club_id))
        games = cursor.fetchall()

        cursor.execute('''
            SELECT player_id, player_name FROM players
            WHERE team = ? AND club_id = ? AND season_year = (
                SELECT season_year FROM seasons WHERE age_group = ? AND date_from = ? LIMIT 1
            )
            ORDER BY player_name ASC
        ''', (team, club_id, team, date_from))
        players = cursor.fetchall()
        player_ids = [row[0] for row in players]

        # Build matrix
        matrix = {}
        for pid in player_ids:
            matrix[pid] = {}
            for game in games:
                gid = game[0]
                game_date = game[1]
                competition = game[2]
                home_team = game[3]
                away_team = game[4]
                cursor.execute('''
                    SELECT SUM(minutes_played) FROM games
                    WHERE player_id=? AND game_date=? AND competition=? AND home_team=? AND away_team=?
                    AND club_id=?
                ''', (pid, game_date, competition, home_team, away_team, club_id))
                res = cursor.fetchone()
                matrix[pid][gid] = res[0] if res and res[0] is not None else 0

        players_obj = [{'id': row[0], 'name': row[1]} for row in players]
        games_obj = []
        for row in games:
            gid, date, competition, home_team, away_team = row
            cursor.execute('''
                SELECT result, COUNT(*) as cnt FROM games
                WHERE game_date=? AND competition=? AND home_team=? AND away_team=?
                AND club_id=?
                GROUP BY result ORDER BY cnt DESC LIMIT 1
            ''', (date, competition, home_team, away_team, club_id))
            res_row = cursor.fetchone()
            result = res_row[0] if res_row and res_row[0] is not None else ''
            games_obj.append({
                'id': gid, 'date': date, 'competition': competition,
                'home_team': home_team, 'away_team': away_team, 'result': result
            })

        conn.close()
        return {'games': games_obj, 'players': players_obj, 'matrix': matrix}
    except Exception as e:
        print(f"Error fetching minutes matrix: {e}")
        return {'games': [], 'players': [], 'matrix': []}


def get_goal_efficiency_per_game(db_path='data/club-stats.db', team="U13", date_from='2025-08-29', date_to='2026-06-08', club_id=1):
    """Get goal efficiency per individual game, sorted by best efficiency first."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                p.player_name,
                g.game_date,
                g.competition,
                g.home_team,
                g.away_team,
                g.goals,
                g.minutes_played,
                ROUND(CAST(g.goals AS FLOAT) / g.minutes_played * 90, 3) as goals_per_90_minutes,
                ROUND(CAST(g.minutes_played AS FLOAT) / g.goals, 2) as minutes_per_goal
            FROM 
                games g
                JOIN players p ON g.player_id = p.player_id AND g.club_id = p.club_id
            WHERE 
                g.game_date BETWEEN ? AND ?
                AND g.age_group = ?
                AND g.club_id = ?
                AND g.goals > 0
                AND g.minutes_played > 0
            ORDER BY 
                goals_per_90_minutes DESC,
                minutes_per_goal ASC,
                g.game_date DESC
        ''', (date_from, date_to, team, club_id))
        results = cursor.fetchall()
        conn.close()
        games = []
        for row in results:
            games.append({
                'player_name': row[0],
                'game_date': row[1],
                'competition': row[2],
                'home_team': row[3],
                'away_team': row[4],
                'goals': row[5],
                'minutes_played': row[6],
                'goals_per_90_minutes': row[7],
                'minutes_per_goal': row[8]
            })
        return games
    except Exception as e:
        print(f"Error fetching goal efficiency per game data: {e}")
        return []


def get_player_overview(db_path='data/club-stats.db', team="U13", date_from='2025-08-29', date_to='2026-06-08',
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

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

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

        cursor.execute(base_query, params)
        results = cursor.fetchall()
        conn.close()

        return [
            {
                'player_name': r[0],
                'games_played': r[1],
                'total_minutes': r[2] or 0,
                'total_goals': r[3] or 0,
                'avg_minutes_per_game': r[4] or 0,
                'avg_goals_per_game': r[5] or 0,
            }
            for r in results
        ]
    except Exception as e:
        print(f"Error fetching player overview: {e}")
        return []


def get_all_player_names(db_path='data/club-stats.db', team="U13", date_from='2025-08-29', date_to='2026-06-08', club_id=1):
    """Return sorted list of player names that have game data in the given season."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT p.player_name
            FROM players p
            JOIN games g ON p.player_id = g.player_id AND g.club_id = p.club_id
            WHERE g.game_date BETWEEN ? AND ?
                AND g.age_group = ? AND p.team = ?
                AND p.club_id = ? AND g.club_id = ?
                AND g.minutes_played > 0
            ORDER BY p.player_name ASC
        ''', (date_from, date_to, team, team, club_id, club_id))
        results = cursor.fetchall()
        conn.close()
        return [r[0] for r in results]
    except Exception as e:
        print(f"Error fetching player names: {e}")
        return []


def get_games_played_per_player(db_path='data/club-stats.db', team="U13", date_from='2025-08-29', date_to='2026-06-08', club_id=1):
    """Get the number of games played per player."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.player_name, COUNT(*) AS num_games
            FROM players p
            JOIN games g ON p.player_id = g.player_id AND g.club_id = p.club_id
            WHERE 
                g.game_date BETWEEN ? AND ?
                AND g.age_group = ? AND p.team = ?
                AND p.club_id = ? AND g.club_id = ?
                AND g.minutes_played > 0
            GROUP BY p.player_id, p.player_name
            ORDER BY num_games DESC
        ''', (date_from, date_to, team, team, club_id, club_id))
        results = cursor.fetchall()
        conn.close()
        players = []
        for row in results:
            players.append({
                'player_name': row[0],
                'num_games': row[1]
            })
        return players
    except Exception as e:
        print(f"Error fetching games played per player data: {e}")
        return []
