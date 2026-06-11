import csv
import re
import unicodedata
from datetime import datetime, timezone
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup


SOURCE_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"
FIFPRO_WORLD11_URL = "https://en.wikipedia.org/wiki/FIFPRO_World_11"
OUTPUT_CSV = "world_cup_rosters.csv"
FIFPRO_NATIONAL_TEAM_BY_NAME = {
    "luis suarez": "Uruguay",
}


def clean_text(value):
    value = re.sub(r"\[[^\]]+\]", "", value or "")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def country_from_flag_image(image_url):
    if not image_url:
        return ""
    filename = unquote(image_url.split("/")[-1])
    filename = re.sub(r"^\d+px-", "", filename)
    filename = re.sub(r"\.(svg|png|jpg|jpeg)$", "", filename, flags=re.IGNORECASE)
    filename = re.sub(r"\.svg$", "", filename, flags=re.IGNORECASE)
    filename = filename.replace("_", " ")
    filename = re.sub(r"^Flag of ", "", filename)
    filename = re.sub(r"^Flag ", "", filename)
    filename = re.sub(r" football\.?", "", filename, flags=re.IGNORECASE)
    filename = re.sub(r" soccer\.?", "", filename, flags=re.IGNORECASE)
    filename = re.sub(r"\s*\(.*?\)", "", filename)
    return clean_text(filename)


def absolute_image_url(image_url):
    if not image_url:
        return ""
    if image_url.startswith("//"):
        return f"https:{image_url}"
    if image_url.startswith("/"):
        return f"https://en.wikipedia.org{image_url}"
    return image_url


def infer_club_country_from_link(club_link):
    if not club_link:
        return ""

    response = requests.get(
        f"https://en.wikipedia.org{club_link}",
        timeout=6,
        headers={"User-Agent": "WorldCupRostersCSV/0.1 (personal research project)"},
    )
    if not response.ok:
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    for category in soup.select("#mw-normal-catlinks a"):
        category_text = clean_text(category.get_text(" ", strip=True))
        match = re.match(r"(?:Association )?Football clubs in (.+)", category_text)
        if match:
            return clean_text(match.group(1))

    infobox = soup.find("table", class_=lambda value: value and "infobox" in value)
    if not infobox:
        return ""

    for row in infobox.select("tr"):
        header = row.find("th")
        data = row.find("td")
        if not header or not data:
            continue
        header_text = clean_text(header.get_text(" ", strip=True)).lower()
        if header_text in {"ground", "stadium", "capacity"}:
            continue
        if header_text in {"league"}:
            flag = data.find("img", src=True)
            country = country_from_flag_image(flag["src"]) if flag else ""
            if country:
                return country

    country_row = infobox.find("th", string=re.compile(r"Country", re.IGNORECASE))
    if country_row:
        data = country_row.find_next_sibling("td")
        if data:
            flag = data.find("img", src=True)
            return country_from_flag_image(flag["src"]) or clean_text(data.get_text(" ", strip=True))

    return ""


def infer_club_logo_from_link(club_link):
    if not club_link:
        return ""

    response = requests.get(
        f"https://en.wikipedia.org{club_link}",
        timeout=20,
        headers={"User-Agent": "WorldCupRostersCSV/0.1 (personal research project)"},
    )
    if not response.ok:
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    infobox = soup.find("table", class_=lambda value: value and "infobox" in value)
    if not infobox:
        return ""

    image = infobox.find("img", src=True)
    return absolute_image_url(image["src"]) if image else ""


def wikipedia_title_from_link(link):
    if not link.startswith("/wiki/"):
        return ""
    return unquote(link.removeprefix("/wiki/"))


def fetch_club_logos_for_links(club_links):
    titles_by_link = {
        link: wikipedia_title_from_link(link)
        for link in club_links
        if wikipedia_title_from_link(link)
    }
    logos = {link: "" for link in club_links}
    titles = list(dict.fromkeys(titles_by_link.values()))

    for index in range(0, len(titles), 50):
        chunk = titles[index : index + 50]
        response = requests.get(
            "https://en.wikipedia.org/w/api.php",
            timeout=30,
            headers={"User-Agent": "WorldCupRostersCSV/0.1 (personal research project)"},
            params={
                "action": "query",
                "format": "json",
                "prop": "pageimages",
                "pithumbsize": "80",
                "redirects": "1",
                "titles": "|".join(chunk),
            },
        )
        if not response.ok:
            continue
        pages = response.json().get("query", {}).get("pages", {})
        logo_by_title = {
            page.get("title", "").replace(" ", "_"): page.get("thumbnail", {}).get("source", "")
            for page in pages.values()
        }
        for link, title in titles_by_link.items():
            logos[link] = logo_by_title.get(title, logos.get(link, ""))

    return logos


def normalized_name(value):
    value = clean_text(value).lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_birth_date_and_age(value):
    value = clean_text(value)
    date_match = re.search(r"\d{4}-\d{2}-\d{2}", value)
    age_match = re.search(r"aged?\s*(\d+)", value)
    birth_date = date_match.group(0) if date_match else value
    age = age_match.group(1) if age_match else ""
    return birth_date, age


def parse_position(value):
    value = clean_text(value)
    match = re.search(r"\b(GK|DF|MF|FW)\b", value)
    return match.group(1) if match else value


def extract_group(heading_text):
    match = re.match(r"Group\s+([A-L])", heading_text)
    return match.group(1) if match else ""


def parse_fifpro_world11():
    response = requests.get(
        FIFPRO_WORLD11_URL,
        timeout=30,
        headers={"User-Agent": "WorldCupRostersCSV/0.1 (personal research project)"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("table", class_="wikitable")
    if not tables:
        return {}

    players = {}
    for tr in tables[0].select("tr")[1:]:
        cells = tr.find_all(["th", "td"])
        if len(cells) < 5:
            continue

        year_match = re.search(r"\d{4}", clean_text(cells[0].get_text(" ", strip=True)))
        if not year_match:
            continue
        year = year_match.group(0)

        for cell in cells[1:5]:
            cell_text = clean_text(cell.get_text(" ", strip=True))
            for player_match in re.finditer(r"([^()]+?)\s*\([^)]*\)", cell_text):
                player = clean_text(player_match.group(1))
                key = normalized_name(player)
                if not key:
                    continue
                players.setdefault(
                    key,
                    {
                        "fifpro_world11_apps": 0,
                        "fifpro_world11_years": [],
                    },
                )
                players[key]["fifpro_world11_apps"] += 1
                players[key]["fifpro_world11_years"].append(year)

    for player in players.values():
        player["fifpro_world11_apps"] = str(player["fifpro_world11_apps"])
        player["fifpro_world11_years"] = ", ".join(player["fifpro_world11_years"])

    return players


def parse_rosters():
    response = requests.get(
        SOURCE_URL,
        timeout=30,
        headers={"User-Agent": "WorldCupRostersCSV/0.1 (personal research project)"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    rows = []
    fifpro_players = parse_fifpro_world11()
    club_countries = {}
    club_links_for_logos = []
    for club_cell in soup.select("table.wikitable td:nth-child(7)"):
        links = club_cell.find_all("a", href=True)
        if links:
            club_links_for_logos.append(links[-1]["href"])
    club_logos = fetch_club_logos_for_links(set(club_links_for_logos))
    current_group = ""
    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for heading in soup.select("h2, h3"):
        heading_text = clean_text(heading.get_text(" ", strip=True))
        group = extract_group(heading_text)
        if heading.name == "h2" and group:
            current_group = group
            continue
        if heading.name != "h3" or not current_group:
            continue

        team = heading_text
        table = heading.find_next("table", class_="wikitable")
        if not table or "wikitable" not in table.get("class", []):
            continue

        for tr in table.select("tr")[1:]:
            cells = tr.find_all(["th", "td"])
            if len(cells) < 7:
                continue

            number = clean_text(cells[0].get_text(" ", strip=True))
            position = parse_position(cells[1].get_text(" ", strip=True))
            player = clean_text(cells[2].get_text(" ", strip=True)).replace(" ( captain )", "")
            birth_date, age = parse_birth_date_and_age(cells[3].get_text(" ", strip=True))
            caps = clean_text(cells[4].get_text(" ", strip=True))
            goals = clean_text(cells[5].get_text(" ", strip=True))
            club_cell = cells[6]
            club = clean_text(club_cell.get_text(" ", strip=True))
            club_flag = club_cell.find("img", src=True)
            club_country = country_from_flag_image(club_flag["src"]) if club_flag else ""
            club_links = club_cell.find_all("a", href=True)
            club_link_tag = club_links[-1] if club_links else None
            club_link = club_link_tag["href"] if club_link_tag else ""
            if not club_country and club_link not in club_countries:
                club_country = infer_club_country_from_link(club_link)
                club_countries[club_link] = club_country
            elif not club_country:
                club_country = club_countries.get(club_link, "")
            club_logo_url = club_logos.get(club_link)
            player_key = normalized_name(player)
            fifpro = fifpro_players.get(player_key, {})
            expected_team = FIFPRO_NATIONAL_TEAM_BY_NAME.get(player_key)
            if expected_team and expected_team != team:
                fifpro = {}

            if not player or player.lower() == "player":
                continue

            rows.append(
                {
                    "group": current_group,
                    "national_team": team,
                    "squad_number": number,
                    "position": position,
                    "player": player,
                    "birth_date": birth_date,
                    "age": age,
                    "caps": caps,
                    "goals": goals,
                    "professional_club": club,
                    "professional_club_country": club_country,
                    "professional_club_logo_url": club_logo_url,
                    "fifpro_world11_apps": fifpro.get("fifpro_world11_apps", "0"),
                    "fifpro_world11_years": fifpro.get("fifpro_world11_years", ""),
                    "all_star_source": FIFPRO_WORLD11_URL if fifpro else "",
                    "contract_source": "",
                    "contract_start": "",
                    "contract_end": "",
                    "salary": "",
                    "salary_currency": "",
                    "source_url": SOURCE_URL,
                    "retrieved_at_utc": retrieved_at,
                }
            )

    return rows


def main():
    rows = parse_rosters()
    fieldnames = [
        "group",
        "national_team",
        "squad_number",
        "position",
        "player",
        "birth_date",
        "age",
        "caps",
        "goals",
        "professional_club",
        "professional_club_country",
        "professional_club_logo_url",
        "fifpro_world11_apps",
        "fifpro_world11_years",
        "all_star_source",
        "contract_source",
        "contract_start",
        "contract_end",
        "salary",
        "salary_currency",
        "source_url",
        "retrieved_at_utc",
    ]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} roster rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
