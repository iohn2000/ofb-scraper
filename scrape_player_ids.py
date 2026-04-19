"""
Scraper for ÖFBV roster page player IDs using Selenium + Firefox.

Usage:
    pip install selenium beautifulsoup4
    # Also ensure geckodriver is installed and on PATH:
    #   https://github.com/mozilla/geckodriver/releases
    #   or: brew install geckodriver  /  sudo apt install firefox-geckodriver

    python scrape_players.py

The script:
1. Opens the team roster page in a headless Firefox browser
2. Finds all player links (vereine.oefb.at/netzwerk/spielerdetails/...)
3. Navigates to each link and waits for the redirect to settle
4. Extracts the numeric player ID from the final URL
5. Prints results as a Python list and saves to players_u13.json
"""

import re
import time
import json

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

TEAM = "U13-A"
TEAM = "U15"
ROSTER_URL = "https://vereine.oefb.at/ScOstbahnXi/Mannschaften/Saison-2025-26/" + TEAM + "/Kader/"
YEAR = 2026


def make_driver(headless: bool = True) -> webdriver.Firefox:
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--width=1280")
    options.add_argument("--height=900")
    # If geckodriver is not on PATH, set the path explicitly:
    # from selenium.webdriver.firefox.service import Service
    # return webdriver.Firefox(service=Service("/path/to/geckodriver"), options=options)
    return webdriver.Firefox(options=options)


def get_player_links(driver: webdriver.Firefox, roster_url: str) -> list[dict]:
    """Load the roster page and collect all spielerdetails links + player names."""
    print(f"Loading roster page: {roster_url}")
    driver.get(roster_url)

    # Wait until at least one spielerdetails link is present
    try:
        WebDriverWait(driver, 15).until(
            lambda d: d.find_elements(By.XPATH, "//a[contains(@href,'spielerdetails')]")
        )
    except Exception:
        print("  Warning: timed out waiting for player links — parsing whatever loaded.")

    soup = BeautifulSoup(driver.page_source, "html.parser")

    player_links = []
    seen_urls = set()

    for a in soup.find_all("a", class_="widget-player_name"):
        href = a.get("href", "")
        if not href:
            continue

        # Make absolute
        if href.startswith("http"):
            full_url = href
        elif href.startswith("/"):
            full_url = "https://vereine.oefb.at" + href
        else:
            full_url = "https://vereine.oefb.at/" + href

        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        name = a.get_text(strip=True)
        player_links.append({"name": name, "url": full_url})

    return player_links


def resolve_player_id(driver: webdriver.Firefox, url: str) -> int | None:
    """
    Navigate to a spielerdetails URL and extract the numeric player ID
    from the final redirected URL (oefb.at/Profile/Spieler/<ID>).
    """
    driver.get(url)

    # Wait for the redirect to complete — the final URL should contain /Spieler/
    try:
        WebDriverWait(driver, 15).until(
            lambda d: re.search(r"/Spieler/(\d+)", d.current_url)
        )
    except Exception:
        pass  # Will try to parse whatever URL we ended up on

    final_url = driver.current_url
    match = re.search(r"/Spieler/(\d+)", final_url)
    if match:
        return int(match.group(1))

    # Fallback: search the page source
    match = re.search(r"/Profile/Spieler/(\d+)", driver.page_source)
    if match:
        return int(match.group(1))

    return None


def scrape_roster(roster_url: str) -> list[dict]:
    driver = make_driver(headless=True)
    try:
        player_links = get_player_links(driver, roster_url)
        print(f"Found {len(player_links)} player links. Resolving IDs...\n")

        players = []
        for i, player in enumerate(player_links, 1):
            print(f"  [{i}/{len(player_links)}] {player['name']} ...")
            player_id = resolve_player_id(driver, player["url"])
            if player_id:
                players.append({
                    "name": player["name"],
                    "id": player_id,
                    "team": TEAM,
                    "year": YEAR,
                })
                print(f"    -> ID: {player_id}")
            else:
                print(f"    -> Could not resolve ID (final URL: {driver.current_url})")
            time.sleep(0.3)  # polite delay

    finally:
        driver.quit()

    return players


def main():
    players = scrape_roster(ROSTER_URL)

    print("\n" + "=" * 60)
    print("RESULT:")
    print("=" * 60)
    print("players = [")
    for p in players:
        print(f'    {{ "name": "{p["name"]}", "id": {p["id"]}, "team": "{p["team"]}", "year": {p["year"]} }},')
    print("]")

    with open(f"{TEAM}-{YEAR}.json", "w", encoding="utf-8") as f:
        json.dump(players, f, ensure_ascii=False, indent=4)
    print(f"\nSaved to: {TEAM}-{YEAR}.json")


if __name__ == "__main__":
    main()