import sqlite3

# Query to find players who scored the most goals in the least amount of minutes per game
query = """
SELECT 
    p.player_name,
    g.game_date,
    g.competition,
    g.home_team,
    g.away_team,
    g.goals,
    g.minutes_played,
    CASE 
        WHEN g.minutes_played > 0 THEN ROUND(CAST(g.goals AS FLOAT) / g.minutes_played * 90, 3)
        ELSE 0
    END as goals_per_90_minutes,
    CASE 
        WHEN g.goals > 0 AND g.minutes_played > 0 THEN ROUND(CAST(g.minutes_played AS FLOAT) / g.goals, 2)
        ELSE NULL
    END as minutes_per_goal
FROM 
    games g
    JOIN players p ON g.player_id = p.player_id
WHERE 
    g.goals > 0
    AND g.minutes_played > 0
ORDER BY 
    goals_per_90_minutes DESC,
    minutes_per_goal ASC,
    g.game_date DESC;
"""

# Execute the query
conn = sqlite3.connect('ofb_stats.db')
cursor = conn.cursor()
cursor.execute(query)
results = cursor.fetchall()

# Print results with headers
print("\n" + "="*140)
print(f"{'Player':<25} {'Date':<20} {'Competition':<20} {'Home Team':<15} {'Away Team':<15} {'Goals':<8} {'Minutes':<10} {'Goals/90min':<15} {'Min/Goal':<12}")
print("="*140)

for row in results:
    player, date, comp, home, away, goals, minutes, goals_per_90, min_per_goal = row
    min_per_goal_str = f"{min_per_goal}" if min_per_goal else "N/A"
    print(f"{player:<25} {date:<20} {comp:<20} {home:<15} {away:<15} {goals:<8} {minutes:<10} {goals_per_90:<15} {min_per_goal_str:<12}")

print("="*140)
print(f"\nTotal games with goals: {len(results)}")
conn.close()
