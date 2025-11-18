"""
Test chart generation from existing database
"""
import sys
sys.path.insert(0, '/Users/fleckj/ofb-scraper')

from scrape_two_step import generate_goals_chart, generate_goals_chart, generate_minutes_chart

# Generate the chart
chart_file = generate_minutes_chart('ofb_stats.db', 'player_minutes.png')
if chart_file:
    print(f"\n✓ Chart generated successfully: {chart_file}")
else:
    print("\n✗ Failed to generate chart")

print("\nGenerating player goals chart...")
goals_chart = generate_goals_chart('ofb_stats.db', 'player_goals.png')
if goals_chart:
       print(f"Goals chart available at: {goals_chart}")