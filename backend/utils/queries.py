import sqlite3
from datetime import datetime

def get_player_minutes(db_path='ofb_stats.db'):
    """
    Get total minutes played per player
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                p.player_name,
                SUM(g.minutes_played) as total_minutes
            FROM players p
            LEFT JOIN games g ON p.player_id = g.player_id
            WHERE g.game_date BETWEEN '2025-08-29' and '2026-06-08'
            GROUP BY p.player_id, p.player_name
            ORDER BY total_minutes DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        player_names = [row[0] for row in results]
        total_minutes = [row[1] if row[1] else 0 for row in results]
        
        return {
            'labels': player_names,
            'data': total_minutes
        }
    except Exception as e:
        print(f"Error fetching minutes data: {e}")
        return {'labels': [], 'data': []}


def get_player_goals(db_path='ofb_stats.db'):
    """
    Get total goals scored per player
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                p.player_name,
                SUM(g.goals) as total_goals
            FROM players p
            LEFT JOIN games g ON p.player_id = g.player_id
            WHERE g.game_date BETWEEN '2025-08-29' and '2026-06-08'
            GROUP BY p.player_id, p.player_name
            HAVING SUM(g.goals) > 0
            ORDER BY total_goals DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        player_names = [row[0] for row in results]
        total_goals = [row[1] if row[1] else 0 for row in results]
        
        return {
            'labels': player_names,
            'data': total_goals
        }
    except Exception as e:
        print(f"Error fetching goals data: {e}")
        return {'labels': [], 'data': []}


def get_player_efficiency(db_path='ofb_stats.db'):
    """
    Get player efficiency stats (goals per 90 minutes, etc.) aggregated across all games
    """
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
                JOIN players p ON g.player_id = p.player_id
            WHERE 
                g.game_date BETWEEN '2025-08-29' and '2026-06-08' and      
                (g.goals > 0 OR g.minutes_played > 0)
            GROUP BY 
                p.player_id, p.player_name
            HAVING 
                SUM(g.goals) > 0
                AND SUM(g.minutes_played) > 0
            ORDER BY 
                goals_per_90_minutes DESC,
                minutes_per_goal ASC
        ''')
        
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


def get_minutes_matrix(db_path='ofb_stats.db'):
    """
    Returns a matrix of all games (x-axis, ordered by date) and all players (y-axis, ordered by name),
    with each cell showing the minutes played by that player in that game (0 if not played).
    Output: {
        'games': [ { 'game_id': ..., 'game_date': ..., ... }, ... ],
        'players': [ 'Player A', 'Player B', ... ],
        'matrix': [ [minA1, minA2, ...], [minB1, minB2, ...], ... ]
    }
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all unique games ordered by date (group by home_team, away_team, game_date)
        cursor.execute('''
            SELECT MIN(id) as id, game_date, competition, home_team, away_team
            FROM games
            WHERE game_date BETWEEN '2025-08-29' and '2026-06-08'
            GROUP BY game_date, competition, home_team, away_team
            ORDER BY game_date ASC, id ASC
        ''')
        games = cursor.fetchall()
        game_ids = [row[0] for row in games]
        game_objs = [
            {
                'id': row[0],
                'date': row[1],
                'competition': row[2],
                'home_team': row[3],
                'away_team': row[4]
            } for row in games
        ]

        # Get all players ordered by name
        cursor.execute('''
            SELECT player_id, player_name FROM players ORDER BY player_name ASC
        ''')
        players = cursor.fetchall()
        player_ids = [row[0] for row in players]
        player_names = [row[1] for row in players]

        # Build matrix: {player_id: {game_id: minutes}}
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
                    SELECT SUM(minutes_played) FROM games WHERE player_id=? AND game_date=? AND competition=? AND home_team=? AND away_team=?
                ''', (pid, game_date, competition, home_team, away_team))
                res = cursor.fetchone()
                matrix[pid][gid] = res[0] if res and res[0] is not None else 0

        # Prepare players and games as objects with id and name/date
        players_obj = [{'id': row[0], 'name': row[1]} for row in players]
        # Add result to games_obj
        games_obj = []
        for row in games:
            gid, date, competition, home_team, away_team = row
            # Find the most common result for this game (across all players)
            cursor.execute('''
                SELECT result, COUNT(*) as cnt FROM games WHERE game_date=? AND competition=? AND home_team=? AND away_team=? GROUP BY result ORDER BY cnt DESC LIMIT 1
            ''', (date, competition, home_team, away_team))
            res_row = cursor.fetchone()
            result = res_row[0] if res_row and res_row[0] is not None else ''
            games_obj.append({'id': gid, 'date': date, 'competition': competition, 'home_team': home_team, 'away_team': away_team, 'result': result})

        conn.close()
        return {
            'games': games_obj,
            'players': players_obj,
            'matrix': matrix
        }
    except Exception as e:
        print(f"Error fetching minutes matrix: {e}")
        return {'games': [], 'players': [], 'matrix': []}

def get_goal_efficiency_per_game(db_path='ofb_stats.db'):
    """
    Get goal efficiency per individual game (goals/90min, min/goal, etc.)
    Sorted by best efficiency first
    """
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
                JOIN players p ON g.player_id = p.player_id
            WHERE 
                g.game_date BETWEEN '2025-08-29' and '2026-06-08' and      
                g.goals > 0
                AND g.minutes_played > 0
            ORDER BY 
                goals_per_90_minutes DESC,
                minutes_per_goal ASC,
                g.game_date DESC
        ''')
        
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

def get_games_played_per_player(db_path='ofb_stats.db'):
    """
    Get the number of games played per player grouped by age group
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT p.player_name, COUNT(*) AS num_games
        FROM 
        players p
        JOIN 
        games g ON p.player_id = g.player_id
        WHERE 
        g.game_date BETWEEN '2025-08-29' and '2026-06-08' 
        and g.minutes_played > 0   
        GROUP BY 
        p.player_id, p.player_name

        ORDER BY 
        num_games desc
        ''')
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