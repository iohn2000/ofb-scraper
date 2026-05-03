#!/usr/bin/env python3
"""
Extract U13-A ranking table from the ÖFBV club portal.
URL: https://vereine.oefb.at/ScOstbahnXi/Mannschaften/Saison-2025-26/U13-A/Tabellen

The ranking data is embedded in the HTML as:
    SG.container.appPreloads['582206667'] = [{ ... "tabellen": { "NORMAL": {"eintraege": [...]} } }]

Available table types: NORMAL (Gesamt), HEIM, AUSWAERTS, HERBST, FRUEHJAHR
Pass one as a CLI argument, or ALL to print every table.
"""

import re
import json
import sys
import requests

URL = "https://vereine.oefb.at/ScOstbahnXi/Mannschaften/Saison-2025-26/U13-A/Tabellen"

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


def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text


def extract_tabellen_data(html: str) -> dict:
    """
    Pull the JSON blob stored in SG.container.appPreloads['582206667'].
    Pattern:  SG.container.appPreloads['582206667']=[{...}];
    """
    pattern = r"SG\.container\.appPreloads\['582206667'\]=(\[.*?\]);"
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        raise ValueError("Could not find appPreloads['582206667'] in page HTML.")
    data = json.loads(match.group(1))
    return data[0]  # array with one item


def print_table(eintraege: list, table_name: str, liga_name: str):
    print(f"\n{'='*72}")
    print(f"  {liga_name}  –  {table_name}")
    print(f"{'='*72}")
    header = (f"{'#':>3}  {'Mannschaft':<32}  "
              f"{'Sp':>3}  {'S':>3}  {'U':>3}  {'N':>3}  "
              f"{'Tore':<9}  {'+/-':>5}  {'Pkt':>4}")
    print(header)
    print("-" * 72)
    for e in eintraege:
        tore = f"{e['toreErzielt']}:{e['toreErhalten']}"
        print(
            f"{e['rang']:>3}  "
            f"{e['mannschaftBezeichnung']:<32}  "
            f"{e['spiele']:>3}  "
            f"{e['siege']:>3}  "
            f"{e['unentschieden']:>3}  "
            f"{e['niederlagen']:>3}  "
            f"{tore:<9}  "
            f"{e['tordifferenz']:>+5}  "
            f"{e['punkte']:>4}"
        )
    print()


def main(table_type: str = "NORMAL"):
    table_type = table_type.upper()
    valid = list(TABLE_TYPES) + ["ALL"]
    if table_type not in valid:
        print(f"Unknown table type '{table_type}'. Choose from: {', '.join(valid)}")
        sys.exit(1)

    print(f"Fetching: {URL}")
    html = fetch_html(URL)
    data = extract_tabellen_data(html)

    liga_name = data.get("bezeichnung", "B-LIGA U13")
    tabellen  = data.get("tabellen", {})

    keys_to_show = list(TABLE_TYPES) if table_type == "ALL" else [table_type]
    for key in keys_to_show:
        if key in tabellen:
            print_table(tabellen[key]["eintraege"], TABLE_TYPES[key], liga_name)
        else:
            print(f"  ['{key}' not present in data]")


if __name__ == "__main__":
    # Usage:  python extract_u13_ranking.py [NORMAL|HEIM|AUSWAERTS|HERBST|FRUEHJAHR|ALL]
    arg = sys.argv[1] if len(sys.argv) > 1 else "NORMAL"
    main(arg)