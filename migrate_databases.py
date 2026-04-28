#!/usr/bin/env python3
"""
One-time migration script: merges ofb_stats.db, susa.db, and fortuna.db
into a single data/club-stats.db with a clubs table and club_id on players+games.

Run once from the project root:
    python migrate_databases.py
"""

import sqlite3
import os

CLUBS = [
    (1, 'Ostbahn XI', 'OstbXI'),
    (2, 'SuSa', 'SuSa'),
    (3, 'Fortuna', 'Fortuna'),
]

SOURCE_DBS = [
    ('data/ofb_stats.db', 1),
    ('data/other-clubs/susa.db', 2),
    ('data/other-clubs/fortuna.db', 3),
]

TARGET_DB = 'data/club-stats.db'


def create_schema(conn):
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clubs (
            id         INTEGER PRIMARY KEY,
            name       TEXT NOT NULL,
            short_name TEXT NOT NULL,
            UNIQUE(name)
        )
    ''')

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

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_player_games
        ON games(player_id, game_date)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_games_club
        ON games(club_id, age_group, game_date)
    ''')

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


def seed_clubs(conn):
    cursor = conn.cursor()
    for club_id, name, short_name in CLUBS:
        cursor.execute(
            'INSERT OR IGNORE INTO clubs (id, name, short_name) VALUES (?, ?, ?)',
            (club_id, name, short_name)
        )
    conn.commit()
    print(f"✓ Seeded {len(CLUBS)} clubs")


def copy_seasons(src_conn, dst_conn):
    cursor = src_conn.cursor()
    dst_cursor = dst_conn.cursor()
    try:
        cursor.execute('SELECT age_group, season_year, date_from, date_to FROM seasons')
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        return 0

    count = 0
    for row in rows:
        dst_cursor.execute(
            'INSERT OR IGNORE INTO seasons (age_group, season_year, date_from, date_to) VALUES (?, ?, ?, ?)',
            row
        )
        if dst_cursor.rowcount:
            count += 1
    dst_conn.commit()
    return count


def copy_players(src_conn, dst_conn, club_id):
    cursor = src_conn.cursor()
    dst_cursor = dst_conn.cursor()

    cursor.execute('SELECT player_id, player_name, team, season_year, last_updated FROM players')
    rows = cursor.fetchall()

    count = 0
    for player_id, player_name, team, season_year, last_updated in rows:
        dst_cursor.execute('''
            INSERT OR IGNORE INTO players
                (club_id, player_id, player_name, team, season_year, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (club_id, player_id, player_name, team, season_year, last_updated))
        if dst_cursor.rowcount:
            count += 1
    dst_conn.commit()
    return count, len(rows)


def copy_games(src_conn, dst_conn, club_id):
    cursor = src_conn.cursor()
    dst_cursor = dst_conn.cursor()

    cursor.execute('''
        SELECT player_id, game_date, competition, age_group, round,
               home_team, away_team, result, minutes_played, goals,
               location, match_link, game_timestamp, last_updated
        FROM games
    ''')
    rows = cursor.fetchall()

    count = 0
    for row in rows:
        (player_id, game_date, competition, age_group, round_,
         home_team, away_team, result, minutes_played, goals,
         location, match_link, game_timestamp, last_updated) = row
        dst_cursor.execute('''
            INSERT OR IGNORE INTO games (
                club_id, player_id, game_date, competition, age_group, round,
                home_team, away_team, result, minutes_played, goals,
                location, match_link, game_timestamp, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (club_id, player_id, game_date, competition, age_group, round_,
              home_team, away_team, result, minutes_played, goals,
              location, match_link, game_timestamp, last_updated))
        if dst_cursor.rowcount:
            count += 1
    dst_conn.commit()
    return count, len(rows)


def main():
    if os.path.exists(TARGET_DB):
        print(f"⚠️  {TARGET_DB} already exists. Delete it first to re-run migration.")
        return

    print(f"Creating {TARGET_DB}...")
    dst_conn = sqlite3.connect(TARGET_DB)
    dst_conn.execute("PRAGMA journal_mode=WAL")

    create_schema(dst_conn)
    seed_clubs(dst_conn)

    for src_path, club_id in SOURCE_DBS:
        club_name = next(c[1] for c in CLUBS if c[0] == club_id)
        print(f"\n→ Migrating {src_path} → club_id={club_id} ({club_name})...")

        if not os.path.exists(src_path):
            print(f"  ✗ File not found: {src_path} — skipping")
            continue

        src_conn = sqlite3.connect(src_path)

        seasons = copy_seasons(src_conn, dst_conn)
        print(f"  Seasons:  {seasons} new")

        p_new, p_total = copy_players(src_conn, dst_conn, club_id)
        print(f"  Players:  {p_new}/{p_total} copied")

        g_new, g_total = copy_games(src_conn, dst_conn, club_id)
        print(f"  Games:    {g_new}/{g_total} copied")

        src_conn.close()

    dst_cursor = dst_conn.cursor()
    dst_cursor.execute("SELECT COUNT(*) FROM players")
    total_players = dst_cursor.fetchone()[0]
    dst_cursor.execute("SELECT COUNT(*) FROM games")
    total_games = dst_cursor.fetchone()[0]
    dst_cursor.execute("SELECT COUNT(*) FROM seasons")
    total_seasons = dst_cursor.fetchone()[0]

    dst_conn.close()
    print(f"\n✓ Migration complete!")
    print(f"  Players: {total_players}, Games: {total_games}, Seasons: {total_seasons}")
    print(f"  Output:  {TARGET_DB}")


if __name__ == '__main__':
    main()
