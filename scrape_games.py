# source ofb/bin/activate

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import json
from datetime import datetime
import sqlite3
import os
from bs4 import BeautifulSoup
import re
import matplotlib.pyplot as plt
import matplotlib
import traceback
matplotlib.use('Agg')  # Use non-interactive backend
import concurrent.futures
import threading

db_write_lock = threading.Lock()

def init_database(db_path):
    """
    Initialize the SQLite database with tables for clubs, players, games and seasons.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clubs (
            id         INTEGER PRIMARY KEY,
            name       TEXT NOT NULL,
            short_name TEXT NOT NULL,
            UNIQUE(name)
        )
    ''')

    # Create players table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            club_id      INTEGER NOT NULL REFERENCES clubs(id),
            player_id    INTEGER NOT NULL,
            player_name  TEXT NOT NULL,
            team         TEXT,
            season_year  INTEGER,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(player_id, team, season_year, club_id)
        )
    ''')

    # Create games table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            club_id        INTEGER NOT NULL REFERENCES clubs(id),
            player_id      INTEGER NOT NULL,
            game_date      TEXT,
            competition    TEXT,
            age_group      TEXT,
            round          INTEGER,
            home_team      TEXT,
            away_team      TEXT,
            result         TEXT,
            minutes_played INTEGER,
            goals          INTEGER,
            location       TEXT,
            match_link     TEXT,
            game_timestamp INTEGER NOT NULL,
            last_updated   TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players (player_id),
            UNIQUE(player_id, game_timestamp, club_id)
        )
    ''')

    # Create indexes for faster queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_player_games
        ON games(player_id, game_date)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_games_club
        ON games(club_id, age_group, game_date)
    ''')

    # Create seasons table for date ranges per team/year
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seasons (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            age_group   TEXT NOT NULL,
            season_year INTEGER NOT NULL,
            date_from   TEXT NOT NULL,
            date_to     TEXT NOT NULL,
            UNIQUE(age_group, season_year)
        )
    ''')

    conn.commit()
    conn.close()
    print(f"✓ Database initialized: {db_path}")

def seed_clubs(db_path):
    """
    Seed the clubs table with known club information.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    clubs = [
        (1, 'Ostbahn XI', 'OstbXI'),
        (2, 'DSG SUSA Vienna', 'SUSA'),
        (3, 'Fortuna 05', 'Fortuna'),
        (4, 'FC 1980 Wien', '1980Wien'),
        (5, 'Mannswörth', 'Mannswoerth'),
    ]

    for club_id, name, short_name in clubs:
       cursor.execute("""
            INSERT INTO clubs (id, name, short_name)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                short_name = excluded.short_name
""", (club_id, name, short_name))

    conn.commit()
    conn.close()
    print(f"✓ Clubs seeded: {len(clubs)} entries")

def seed_seasons(db_path):
    """
    Seed the seasons table with known season date ranges.
    Each season runs roughly from late August to early June.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    known_seasons = [
        ('U13', 2026, '2025-08-29', '2026-06-08'),
        ('U14', 2026, '2025-08-29', '2026-06-08'),
        ('U15', 2026, '2025-08-29', '2026-06-08'),
    ]

    for age_group, year, date_from, date_to in known_seasons:
        cursor.execute('''
            INSERT OR IGNORE INTO seasons (age_group, season_year, date_from, date_to)
            VALUES (?, ?, ?, ?)
        ''', (age_group, year, date_from, date_to))

    conn.commit()
    conn.close()
    print(f"✓ Seasons seeded: {len(known_seasons)} entries")


def save_player_to_db(player_id, player_name, team, year, db_path, club_id=1):
    """
    Save or update player information in the database
    """
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO players (club_id, player_id, player_name, team, season_year, last_updated)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(player_id, team, season_year, club_id) DO UPDATE SET
            player_name  = excluded.player_name,
            last_updated = CURRENT_TIMESTAMP
    ''', (club_id, player_id, player_name, team, year))   
    
    conn.commit()
    conn.close()


def save_games_to_db(player_id, games_data, db_path='data/club-stats.db', club_id=1):
    """
    Save or update game statistics in the database
    Returns number of new games added and updated
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    new_games = 0
    updated_games = 0
    
    for game in games_data:
        timestamp = game.get('anstoss', 0)
        
        # Parse date and convert to ISO string for SQLite
        if timestamp:
            game_date_obj = datetime.fromtimestamp(timestamp / 1000)
            game_date = game_date_obj.strftime('%Y-%m-%d %H:%M:%S')
        else:
            game_date = None
        
        # Check if game already exists for this player and club
        cursor.execute(
            'SELECT id FROM games WHERE player_id = ? AND game_timestamp = ? AND club_id = ?',
            (player_id, timestamp, club_id)
        )
        existing = cursor.fetchone()
        
        minutes = game.get('einsatzMinuten', '0')
        goals = game.get('tore', '0')
        
        # Convert to int, default to 0 if not numeric
        minutes_int = int(minutes) if str(minutes).isdigit() else 0
        goals_int = int(goals) if str(goals).isdigit() else 0
        
        if existing:
            # Update existing game for this player
            cursor.execute('''
                UPDATE games SET
                    competition = ?,
                    age_group = ?,
                    round = ?,
                    home_team = ?,
                    away_team = ?,
                    result = ?,
                    minutes_played = ?,
                    goals = ?,
                    location = ?,
                    match_link = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE player_id = ? AND game_timestamp = ? AND club_id = ?
            ''', (
                game.get('bewerb', ''),
                game.get('ageGroup', ''),
                game.get('runde', 0),
                game.get('heimMannschaft', ''),
                game.get('gastMannschaft', ''),
                game.get('ergebnis', ''),
                minutes_int,
                goals_int,
                game.get('spielortBezeichnung', ''),
                game.get('actionLink', ''),
                player_id,
                timestamp,
                club_id
            ))
            updated_games += 1
        else:
            # Insert new game
            cursor.execute('''
                INSERT INTO games (
                    club_id, player_id, game_date, competition, age_group, round,
                    home_team, away_team, result, minutes_played,
                    goals, location, match_link, game_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                club_id,
                player_id,
                game_date,
                game.get('bewerb', ''),
                game.get('ageGroup', ''),
                game.get('runde', 0),
                game.get('heimMannschaft', ''),
                game.get('gastMannschaft', ''),
                game.get('ergebnis', ''),
                minutes_int,
                goals_int,
                game.get('spielortBezeichnung', ''),
                game.get('actionLink', ''),
                timestamp
            ))
            new_games += 1
    
    conn.commit()
    conn.close()
    
    return new_games, updated_games


def generate_minutes_chart(db_path='data/club-stats.db', output_file='player_minutes.png', team="U13"):
    """
    Generate a bar chart showing total minutes played for each player
    Saves the chart as a PNG file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query to get total minutes per player
    cursor.execute('''
        SELECT 
            p.player_name,
            SUM(g.minutes_played) as total_minutes
        FROM players p
        LEFT JOIN games g ON p.player_id = g.player_id
        WHERE 
            g.game_date BETWEEN '2025-08-29' and '2026-06-08'
            AND p.team = ?       
        GROUP BY p.player_id, p.player_name
        ORDER BY total_minutes DESC
    ''', (team,))
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        print("No data found in database to generate chart")
        return None
    
    # Separate player names and minutes
    player_names = [row[0] for row in results]
    total_minutes = [row[1] if row[1] else 0 for row in results]
    
    # Create horizontal bar chart
    plt.figure(figsize=(10, 8))
    bars = plt.barh(player_names, total_minutes, color='steelblue', edgecolor='navy', linewidth=1.5)
    
    # Add value labels at the end of bars
    for bar, minutes in zip(bars, total_minutes):
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2.,
                f' {int(minutes)}',
                ha='left', va='center', fontsize=10, fontweight='bold')
    
    plt.ylabel('Player', fontsize=12, fontweight='bold')
    plt.xlabel('Total Minutes Played', fontsize=12, fontweight='bold')
    plt.title('ÖFB '' + team+ '' - Total Minutes Played by Player', fontsize=14, fontweight='bold', pad=20)
    plt.grid(axis='x', alpha=0.3, linestyle='--')
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Chart saved to: {output_file}")
    return output_file


def scrape_from_page(player_id, team, year=2026):
    """
    Visit the player page with Firefox and extract data directly from the loaded page
    """
    url = f"https://www.oefb.at/Profile/Spieler/{player_id}/{team}"
    
    print(f"Visiting page with Firefox to extract player data...")
    print(f"URL: {url}")
    
    firefox_options = Options()
    # Comment out headless mode to watch the browser
    # firefox_options.add_argument('--headless')
    
    driver = None
    
    try:
        driver = webdriver.Firefox(options=firefox_options)
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Handle cookie consent popup
        print("Checking for cookie consent popup...")
        try:
            # Wait for cookie popup and try different possible selectors
            time.sleep(1)
            
            # Try the specific ÖFB cookie accept button first
            cookie_selectors = [
                "input[type='button'][onclick*='oefb3CookieConsent.accept']",  # ÖFB specific
                "input[value*='Alle Cookies akzeptieren']",  # By button text
                "input[value*='akzeptieren']",  # Partial match
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    cookie_button.click()
                    print(f"✓ Cookie consent accepted using selector: {selector}")
                    time.sleep(1)
                    break
                except:
                    continue
        except Exception as e:
            print(f"No cookie popup found or already accepted: {e}")
        
        # Scroll to trigger any lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Click the specific link that triggers the JavaScript function to load player stats
        print(f"Looking for player stats trigger link for year {year}...")
        try:
            # Look for the link with the onclick event that calls loadSpieler
            # The link should have class "open_close_url_1" and title matching the season
            link_selector = f"a.open_close_url_1[title*='{year}']"
            stats_link = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, link_selector))
            )
            
            print(f"✓ Found stats link: {stats_link.get_attribute('title')}")
            print(f"  onclick: {stats_link.get_attribute('onclick')}")
            
            # Click the link to trigger the JavaScript function
            stats_link.click()
            print("✓ Clicked stats link to trigger JSON generation")
            time.sleep(2)
        except Exception as e:
            print(f"⚠ Could not find or click stats link: {e}")
            # Fallback: try clicking any open_close_url_1 links
            try:
                containers = driver.find_elements(By.CSS_SELECTOR, ".open_close_url_1")
                print(f"Found {len(containers)} open_close_url_1 elements, clicking all...")
                for container in containers:
                    try:
                        driver.execute_script("arguments[0].click();", container)
                        time.sleep(1)
                    except:
                        pass
            except:
                pass
        
        # Wait longer for AJAX calls to complete and data to be loaded
        print("Waiting for AJAX to complete...")
        time.sleep(3)
        
        # Get the page source after JavaScript execution
        htmlResult = driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML")
        page_source = htmlResult #driver.page_source
        
       
        driver.quit()
        
        # Parse the rendered HTML to extract game data
        print("Parsing rendered HTML for game data...")
        games_data = []
        
        try:
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find all game rows - they follow the pattern of div classes c0, c1, c2, c3, c4, c5, c6
            # Each game is represented by a set of these divs
            
            # Find the container with the game data
            # Look for divs with class starting with 'c' followed by a number
            all_divs = soup.find_all('div', class_=re.compile(r'^c\d+'))
            
            print(f"Found {len(all_divs)} data divs")
            
            # Group divs into games (each game has 7 divs: c0-c6)
            current_game = {}
            
            for div in all_divs:
                classes = div.get('class', [])
                
                # Find which column this is (c0, c1, c2, etc.)
                col_class = None
                for cls in classes:
                    if cls.startswith('c') and len(cls) == 2 and cls[1].isdigit():
                        col_class = cls
                        break
                
                if not col_class:
                    continue
                
                # Extract text from the div
                text_span = div.find('span', class_='m_g_text_1')
                text = text_span.get_text(strip=True) if text_span else ''
                
                # Map columns to data fields
                if col_class == 'c0':  # Date/Time
                    if current_game:  # Save previous game if exists
                        games_data.append(current_game)
                    current_game = {'datum': text}
                    
                elif col_class == 'c1':  # Competition (Bewerb)
                    current_game['bewerb'] = text
                    
                elif col_class == 'c2':  # Round (Runde)
                    current_game['runde'] = int(text) if text.isdigit() else 0
                    
                elif col_class == 'c3':  # Teams (a vs b)
                    # Extract from link title or text
                    link = div.find('a')
                    if link:
                        title = link.get('title', '')
                        if ' - ' in title:
                            teams = title.split(' - ')
                            current_game['heimMannschaft'] = teams[0].strip()
                            current_game['gastMannschaft'] = teams[1].strip()
                        current_game['actionLink'] = link.get('href', '')
                    else:
                        current_game['heimMannschaft'] = text
                        current_game['gastMannschaft'] = ''
                    
                elif col_class == 'c4':  # Result (Ergebnis)
                    current_game['ergebnis'] = text
                    
                elif col_class == 'c5':  # Minutes (Einsatzminuten)
                    current_game['einsatzMinuten'] = int(text) if text.isdigit() else 0
                    
                elif col_class == 'c6':  # Goals (Tore)
                    current_game['tore'] = int(text) if text.isdigit() else 0
            
            # Don't forget to add the last game
            if current_game and 'datum' in current_game:
                games_data.append(current_game)
            
            # Process each game to extract age group and parse date properly
            for game in games_data:
                datum_str = game.get('datum', '')
                bewerb = game.get('bewerb', '')
                game['ageGroup'] = team

                # Parse date from format: "DD.MM.YYYY, HH:MM Uhr" to timestamp
                # Example: "15.11.2025, 11:30 Uhr"
                if datum_str and '.' in datum_str:
                    try:
                        # Remove " Uhr" suffix and split by comma
                        date_part = datum_str.replace(' Uhr', '').strip()
                        # Parse: "DD.MM.YYYY, HH:MM"
                        date_obj = datetime.strptime(date_part, '%d.%m.%Y, %H:%M')
                        # Convert to timestamp in milliseconds (like ÖFB uses)
                        game['anstoss'] = int(date_obj.timestamp() * 1000)
                    except Exception as e:
                        print(f"Warning: Could not parse date '{datum_str}': {e}")
                        game['anstoss'] = 0
                else:
                    game['anstoss'] = 0
            
            print(f"✓ Extracted {len(games_data)} games from rendered HTML")
            
            # Display sample data
            if games_data:
                print(f"Sample game: {games_data[0]}")
            
        except Exception as e:
            print(f"Error parsing HTML: {e}")
            traceback.print_exc()
        
        return games_data
        
    except Exception as e:
        print(f"Error visiting page: {e}")
        traceback.print_exc()
        if driver:
            driver.quit()
        return None

def scrape_player_stats(player_id, team, year=2026, skip_trigger=False):
    """
    Complete scraping process:
    Extract data from rendered HTML in the browser
    
    Args:
        player_id: The player's ID
        team: Team category
        year: Season year
        skip_trigger: Ignored (kept for compatibility)
    """
    games_data = scrape_from_page(player_id, team, year)
    
    if not games_data:
        print("Failed to extract data from page")
        return None
    
    # Convert to expected format
    return {'spieleAlle': games_data}


def save_player_stats_to_db(player_id, player_name, team, year, data, db_path, club_id=1):
    """
    Save player statistics to database
    Returns tuple: (new_games_count, updated_games_count)
    """
    if not data or 'spieleAlle' not in data:
        return 0, 0
    
    games = data['spieleAlle']
    
    # Save player to database
    save_player_to_db(player_id, player_name, team, year, db_path, club_id)
    
    # Save games to database
    new_games, updated_games = save_games_to_db(player_id, games, db_path, club_id)
    
    return new_games, updated_games


def print_player_stats(player_id, player_name, team, year=2026, skip_trigger=False):
    """
    Fetch and display player statistics to console
    """
    print("=" * 80)
    print(f"Player: {player_name} (ID: {player_id})")
    print(f"Team: {team}, Season: {year}")
    print("=" * 80)
    
    data = scrape_player_stats(player_id, team, year, skip_trigger=skip_trigger)
    
    if not data or 'spieleAlle' not in data:
        print("\n✗ Failed to fetch data or no games found")
        return None
    
    games = data['spieleAlle']
    print(f"\n✓ Found {len(games)} games\n")
    
    for i, game in enumerate(games, 1):
        # Parse timestamp
        timestamp = game.get('anstoss', 0)
        if timestamp:
            date_obj = datetime.fromtimestamp(timestamp / 1000)
            datum = date_obj.strftime('%d.%m.%Y, %H:%M Uhr')
        else:
            datum = ''
        
        heim = game.get('heimMannschaft', '')
        gast = game.get('gastMannschaft', '')
        spiel = f"{heim} - {gast}"
        
        print(f"Game {i}: {spiel}  - Player: {player_name} - Minutes: {game.get('einsatzMinuten', '')} - Goals: {game.get('tore', '')}")
    
    return data



def process_player(player, db_path, club_id=1):
    """
    Worker function: scrape one player and save to DB.
    Designed to run in a thread pool — each call opens its own Firefox instance.
    """
    player_id   = player['id']
    player_name = player['name']
    team        = player['team']
    year        = player['year']

    print(f"[{player_name}] Starting scrape...")

    try:
        data = scrape_player_stats(player_id, team, year, skip_trigger=False)

        if not data or 'spieleAlle' not in data:
            print(f"[{player_name}] ✗ No data returned")
            return player_name, 0, 0

        games = data['spieleAlle']
        print(f"[{player_name}] ✓ Found {len(games)} games")

        # Serialize DB writes to avoid SQLite "database is locked" errors
        with db_write_lock:
            new_games, updated_games = save_player_stats_to_db(
                player_id, player_name, team, year, data, db_path, club_id
            )

        print(f"[{player_name}] ✓ DB: {new_games} new, {updated_games} updated")
        return player_name, new_games, updated_games

    except Exception as e:
        print(f"[{player_name}] ✗ Error: {e}")
        traceback.print_exc()
        return player_name, 0, 0



if __name__ == "__main__":
   import argparse

   parser = argparse.ArgumentParser(description='ÖFB Player Statistics Scraper')
   parser.add_argument('players_file', default='data/u13-a-2026.json', help='Path to JSON file containing player list (e.g. data/u13-a-2026.json)')
   parser.add_argument('--db', default='data/club-stats.db', help='SQLite database path (default: data/club-stats.db)')
   parser.add_argument('--club-id', type=int, default=1, help='Club ID to associate scraped data with (1=Ostbahn XI, 2=SuSa, 3=Fortuna; default: 1)')
   parser.add_argument('--workers', default=3, type=int, help='Number of parallel Firefox instances (default: 3)')
   args = parser.parse_args()

   # Load players
   try:
       with open(args.players_file, 'r', encoding='utf-8') as f:
           players = json.load(f)
       print(f"✓ Loaded {len(players)} players from {args.players_file}")
   except FileNotFoundError:
       print(f"✗ File not found: {args.players_file}")
       exit(1)
   except json.JSONDecodeError as e:
       print(f"✗ Invalid JSON in {args.players_file}: {e}")
       exit(1)

   # Enable WAL mode so SQLite handles concurrent reads gracefully
   conn = sqlite3.connect(args.db)
   conn.execute("PRAGMA journal_mode=WAL")
   conn.close()
   init_database(args.db)
   seed_seasons(args.db)
   seed_clubs(args.db)

   print(f"\nStarting parallel scrape with {args.workers} workers (club_id={args.club_id})...\n")
   print("=" * 80)

   results = []
   with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
       futures = {
           executor.submit(process_player, player, args.db, args.club_id): player['name']
           for player in players
       }
       for future in concurrent.futures.as_completed(futures):
           player_name = futures[future]
           try:
               result = future.result()
               results.append(result)
           except Exception as e:
               print(f"[{player_name}] ✗ Unhandled exception: {e}")
    # Summary
    
   print("\n" + "=" * 80)
   print(f"All {len(players)} players processed!")
   total_new     = sum(r[1] for r in results)
   total_updated = sum(r[2] for r in results)
   print(f"Total: {total_new} new games, {total_updated} updated across all players")
   print("=" * 80)