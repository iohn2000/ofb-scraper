import sqlite3

# Query to find players with the most goals per minute across all their games
query = """
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
    g.goals > 0
    OR g.minutes_played > 0
GROUP BY 
    p.player_id, p.player_name
HAVING 
    SUM(g.goals) > 0
    AND SUM(g.minutes_played) > 0
ORDER BY 
    goals_per_90_minutes DESC,
    minutes_per_goal ASC;
"""

# Execute the query
conn = sqlite3.connect('ofb_stats.db')
cursor = conn.cursor()
cursor.execute(query)
results = cursor.fetchall()

# Print results with headers
print("\n" + "="*130)
print(f"{'Player':<25} {'Games':<8} {'Goals':<8} {'Minutes':<10} {'Goals/90min':<15} {'Min/Goal':<12} {'Goals/Game':<12}")
print("="*130)

for row in results:
    player, games, goals, minutes, goals_per_90, min_per_goal, goals_per_game = row
    print(f"{player:<25} {games:<8} {goals:<8} {minutes:<10} {goals_per_90:<15} {min_per_goal:<12} {goals_per_game:<12}")

print("="*130)
print(f"\nTotal players: {len(results)}")
conn.close()
