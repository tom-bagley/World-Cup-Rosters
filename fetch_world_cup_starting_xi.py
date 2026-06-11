import csv
import re

import requests
from bs4 import BeautifulSoup


SOURCE_URL = "https://mylineups.app/world-cup-2026/"
OUTPUT_CSV = "world_cup_starting_xi.csv"
HEADERS = {"User-Agent": "WorldCupRosters/0.1 (personal research project)"}
LINEUP_ROLES = {"GK", "DEF", "MID", "ATT"}


def fetch_soup(url):
    response = requests.get(url, timeout=20, headers=HEADERS)
    response.raise_for_status()
    response.encoding = "utf-8"
    return BeautifulSoup(response.text, "html.parser")


def page_lines(soup):
    return [line.strip() for line in soup.get_text("\n").splitlines() if line.strip()]


def team_pages():
    soup = fetch_soup(SOURCE_URL)
    pages = []

    for link in soup.select("a[href]"):
        href = link["href"]
        if "/world-cup-2026/teams/" not in href:
            continue

        url = href if href.startswith("http") else f"https://mylineups.app{href}"
        team = link.get_text(" ", strip=True)
        if team and (team, url) not in pages:
            pages.append((team, url))

    return pages


def parse_team_page(team, url):
    lines = page_lines(fetch_soup(url))
    formation = ""
    group = ""

    for index, line in enumerate(lines):
        group_match = re.search(r"World Cup 2026\s+.\s+Group\s+([A-L])", line)
        if group_match:
            group = group_match.group(1)

        previous_line = lines[index - 1] if index else ""
        if previous_line == team and re.fullmatch(r"\d(?:-\d)+", line):
            formation = line

    start_index = lines.index("15 bench") + 1 if "15 bench" in lines else lines.index("11 starters") + 1
    starters = []
    index = start_index

    while index + 2 < len(lines) and len(starters) < 11:
        role, shirt_number, player_name = lines[index], lines[index + 1], lines[index + 2]
        if role in LINEUP_ROLES and shirt_number.isdigit():
            starters.append((role, shirt_number, player_name))
            index += 3
        else:
            index += 1

    if len(starters) != 11:
        raise ValueError(f"Expected 11 starters for {team}, found {len(starters)}")

    return [
        {
            "team": team,
            "group": group,
            "formation": formation,
            "starter_order": order,
            "lineup_role": role,
            "shirt_number": shirt_number,
            "player_name": player_name,
            "source_url": url,
        }
        for order, (role, shirt_number, player_name) in enumerate(starters, start=1)
    ]


def main():
    rows = []
    pages = team_pages()

    for team, url in pages:
        rows.extend(parse_team_page(team, url))

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "team",
                "group",
                "formation",
                "starter_order",
                "lineup_role",
                "shirt_number",
                "player_name",
                "source_url",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} starters from {len(pages)} teams to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
