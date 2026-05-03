"""
Fetch B-Liga ranking data on-the-fly from ÖFBV club portal.
Used by the ranking API endpoint.
"""

import re
import json
import requests
from typing import Dict, List, Optional


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de-AT,de;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://vereine.oefb.at/",
}

TABLE_TYPES = {
    "NORMAL":    "Gesamt",
    "HEIM":      "Heim",
    "AUSWAERTS": "Auswärts",
    "HERBST":    "Herbst",
    "FRUEHJAHR": "Frühjahr",
}

TEAM_URLS = {
    "U13": "https://vereine.oefb.at/ScOstbahnXi/Mannschaften/Saison-2025-26/U13-A/Tabellen",
    "U14": "https://vereine.oefb.at/ScOstbahnXi/Mannschaften/Saison-2025-26/U14-A/Tabellen",
    "U15": "https://vereine.oefb.at/ScOstbahnXi/Mannschaften/Saison-2025-26/U15-A/Tabellen",
}


def fetch_html(url: str) -> str:
    """Fetch HTML from given URL."""
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text


def extract_tabellen_data(html: str) -> dict:
    """Extract ranking JSON from HTML."""
    pattern = r"SG\.container\.appPreloads\['582206667'\]=(\[.*?\]);"
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        raise ValueError("Could not find ranking data in page HTML.")
    data = json.loads(match.group(1))
    return data[0]


def get_ranking(team: str = "U13", table_type: str = "NORMAL") -> Dict:
    """
    Fetch ranking for a specific team and table type.
    
    Args:
        team: Age group (U13, U14, U15)
        table_type: NORMAL, HEIM, AUSWAERTS, HERBST, FRUEHJAHR
        
    Returns:
        Dict with ranking data and metadata
    """
    team = team.upper()
    table_type = table_type.upper()
    
    if team not in TEAM_URLS:
        return {"error": f"Team '{team}' not supported. Available: {', '.join(TEAM_URLS.keys())}"}
    
    if table_type not in TABLE_TYPES:
        return {"error": f"Table type '{table_type}' not supported. Available: {', '.join(TABLE_TYPES.keys())}"}
    
    try:
        url = TEAM_URLS[team]
        html = fetch_html(url)
        data = extract_tabellen_data(html)
        
        liga_name = data.get("bezeichnung", f"B-LIGA {team}")
        tabellen = data.get("tabellen", {})
        
        if table_type not in tabellen:
            return {
                "error": f"Table type '{table_type}' not available for {team}",
                "available_types": list(tabellen.keys()),
                "liga_name": liga_name
            }
        
        entries = tabellen[table_type].get("eintraege", [])
        
        # Format entries for frontend
        formatted_entries = []
        for entry in entries:
            formatted_entries.append({
                "rang": entry.get("rang"),
                "mannschaftBezeichnung": entry.get("mannschaftBezeichnung"),
                "spiele": entry.get("spiele"),
                "siege": entry.get("siege"),
                "unentschieden": entry.get("unentschieden"),
                "niederlagen": entry.get("niederlagen"),
                "toreErzielt": entry.get("toreErzielt"),
                "toreErhalten": entry.get("toreErhalten"),
                "tordifferenz": entry.get("tordifferenz"),
                "punkte": entry.get("punkte"),
            })
        
        return {
            "success": True,
            "liga_name": liga_name,
            "team": team,
            "table_type": table_type,
            "table_type_label": TABLE_TYPES[table_type],
            "entries": formatted_entries,
            "available_types": list(TABLE_TYPES.keys()),
        }
    
    except requests.RequestException as e:
        return {"error": f"Failed to fetch ranking data: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse ranking data: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def get_available_table_types() -> Dict[str, str]:
    """Return available table types mapping."""
    return TABLE_TYPES
