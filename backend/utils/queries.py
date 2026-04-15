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
                g.goals > 0
                OR g.minutes_played > 0
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
