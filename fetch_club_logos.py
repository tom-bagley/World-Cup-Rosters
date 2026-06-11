import argparse
import csv
import hashlib
import json
import mimetypes
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

import requests
from bs4 import BeautifulSoup


ROSTERS_CSV = Path("world_cup_rosters.csv")
SOURCE_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"
WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
THESPORTSDB_TEAM_SEARCH_URL = "https://www.thesportsdb.com/api/v1/json/3/searchteams.php"
GITHUB_LOGO_TREE_URL = "https://api.github.com/repos/luukhopman/football-logos/git/trees/master?recursive=1"
GITHUB_LOGO_RAW_BASE = "https://raw.githubusercontent.com/luukhopman/football-logos/master/"
FOOTYLOGOS_BASE_URL = "https://www.footylogos.com"
CLUB_LOGO_CACHE = Path("club_logo_cache.json")
CLUB_LOGO_DIR = Path("club_logo_cache")
USER_AGENT = "WorldCupRostersLogoCache/1.0 (personal research project)"


def clean_text(value):
    value = re.sub(r"\[[^\]]+\]", "", value or "")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalized_name(value):
    value = clean_text(value).lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def without_club_suffix(value):
    value = normalized_name(value)
    value = re.sub(r"\b(a f c|afc|f c|fc|s c|sc|c f|cf|f k|fk|s k|sk|j k|jk)\b$", "", value)
    return re.sub(r"\s+", " ", value).strip()


def absolute_image_url(image_url):
    if not image_url:
        return ""
    if image_url.startswith("//"):
        return f"https:{image_url}"
    if image_url.startswith("/"):
        return f"https://en.wikipedia.org{image_url}"
    return image_url


def wikipedia_path(url_or_path):
    if not url_or_path:
        return ""
    if url_or_path.startswith("/wiki/"):
        return url_or_path
    parsed = urlparse(url_or_path)
    if parsed.netloc.endswith("wikipedia.org") and parsed.path.startswith("/wiki/"):
        return parsed.path
    return ""


def wikipedia_title_from_link(link):
    link = wikipedia_path(link)
    if not link:
        return ""
    return unquote(link.removeprefix("/wiki/"))


def club_name_candidates(club_name, link):
    title = wikipedia_title_from_link(link).replace("_", " ")
    values = [club_name, title, re.sub(r"\s*\([^)]*\)", "", title)]

    candidates = []
    for value in values:
        for candidate in [normalized_name(value), without_club_suffix(value)]:
            if candidate and candidate not in candidates:
                candidates.append(candidate)
    return candidates


def slug_candidates(club_name, link):
    candidates = []
    for value in club_name_candidates(club_name, link):
        slug = value.replace(" ", "-")
        if slug and slug not in candidates:
            candidates.append(slug)

    title = wikipedia_title_from_link(link)
    raw_values = [
        club_name,
        title.replace("_", " "),
        re.sub(r"\s*\([^)]*\)", "", title.replace("_", " ")),
    ]
    for value in raw_values:
        value = clean_text(value)
        value = unicodedata.normalize("NFKD", value)
        value = "".join(char for char in value if not unicodedata.combining(char))
        value = value.lower()
        value = value.replace("&", " and ")
        value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
        if value and value not in candidates:
            candidates.append(value)
    return candidates


def load_club_logo_cache():
    if not CLUB_LOGO_CACHE.exists():
        return {}
    with CLUB_LOGO_CACHE.open("r", encoding="utf-8") as cache_file:
        data = json.load(cache_file)
    if not isinstance(data, dict):
        return {}
    return {
        wikipedia_path(link): value
        for link, value in data.items()
        if wikipedia_path(link) and isinstance(value, str)
    }


def save_club_logo_cache(cache):
    with CLUB_LOGO_CACHE.open("w", encoding="utf-8") as cache_file:
        json.dump(dict(sorted(cache.items())), cache_file, indent=2, ensure_ascii=False)
        cache_file.write("\n")


def cached_logo_exists(path):
    return bool(path) and Path(path).exists()


def logo_extension(url, content_type=""):
    content_type = content_type.split(";")[0].strip()
    content_ext = mimetypes.guess_extension(content_type) if content_type else ""
    if content_ext in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}:
        return ".jpg" if content_ext == ".jpeg" else content_ext

    path_ext = Path(urlparse(url).path).suffix.lower()
    if path_ext in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}:
        return ".jpg" if path_ext == ".jpeg" else path_ext
    return ".png"


def local_logo_path(link, image_url, response):
    title = wikipedia_title_from_link(link) or "club-logo"
    slug = re.sub(r"[^a-z0-9]+", "-", normalized_name(title)).strip("-") or "club-logo"
    digest = hashlib.sha1(link.encode("utf-8")).hexdigest()[:10]
    extension = logo_extension(image_url, response.headers.get("Content-Type", ""))
    return CLUB_LOGO_DIR / f"{slug}-{digest}{extension}"


def cache_logo_image(link, image_url):
    if not image_url:
        return ""

    response = requests.get(image_url, timeout=12, headers={"User-Agent": USER_AGENT})
    if not response.ok or not response.content:
        return ""

    CLUB_LOGO_DIR.mkdir(exist_ok=True)
    logo_path = local_logo_path(link, image_url, response)
    logo_path.write_bytes(response.content)
    return logo_path.as_posix()


def club_links_from_csv():
    if not ROSTERS_CSV.exists():
        return {}

    clubs = {}
    with ROSTERS_CSV.open("r", encoding="utf-8-sig", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            link = wikipedia_path(row.get("professional_club_wikipedia_url", ""))
            name = clean_text(row.get("professional_club", ""))
            if link and name:
                clubs[link] = name
    return clubs


def club_links_from_source_page():
    response = requests.get(SOURCE_URL, timeout=30, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    clubs = {}
    for club_cell in soup.select("table.wikitable td:nth-child(7)"):
        links = club_cell.find_all("a", href=True)
        if not links:
            continue
        link = wikipedia_path(links[-1]["href"])
        name = clean_text(club_cell.get_text(" ", strip=True))
        if link and name:
            clubs[link] = name
    return clubs


def pageimage_logos(club_links):
    titles_by_link = {
        link: wikipedia_title_from_link(link)
        for link in club_links
        if wikipedia_title_from_link(link)
    }
    logos = {}
    titles = list(dict.fromkeys(titles_by_link.values()))

    for index in range(0, len(titles), 50):
        response = requests.get(
            WIKIPEDIA_API_URL,
            timeout=30,
            headers={"User-Agent": USER_AGENT},
            params={
                "action": "query",
                "format": "json",
                "prop": "pageimages",
                "pithumbsize": "120",
                "redirects": "1",
                "titles": "|".join(titles[index : index + 50]),
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
            if logo_by_title.get(title):
                logos[link] = logo_by_title[title]

    return logos


def footylogos_png_for_club(club_name, link):
    for slug in slug_candidates(club_name, link):
        response = requests.get(
            f"{FOOTYLOGOS_BASE_URL}/logos/{slug}",
            timeout=8,
            headers={"User-Agent": USER_AGENT},
        )
        if response.status_code == 404:
            continue
        if not response.ok:
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        page_title = clean_text(soup.find("h1").get_text(" ", strip=True)) if soup.find("h1") else ""
        if " logo" not in page_title.lower() and " badge" not in page_title.lower():
            continue

        for link_tag in soup.find_all("a", href=True):
            label = clean_text(link_tag.get_text(" ", strip=True)).lower()
            href = link_tag["href"]
            if "download png" in label and href.startswith("http"):
                return href
    return ""


def footylogos_logo_urls(clubs):
    logos = {}
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {
            executor.submit(footylogos_png_for_club, club_name, link): link
            for link, club_name in clubs.items()
        }
        for future in as_completed(futures):
            link = futures[future]
            try:
                logos[link] = future.result()
            except requests.RequestException:
                logos[link] = ""
    return {link: logo for link, logo in logos.items() if logo}


def github_logo_index():
    response = requests.get(GITHUB_LOGO_TREE_URL, timeout=30, headers={"User-Agent": USER_AGENT})
    if not response.ok:
        return {}

    logos = {}
    for item in response.json().get("tree", []):
        path = item.get("path", "")
        if not path.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".svg")):
            continue
        if not path.startswith("logos/"):
            continue

        name = Path(path).stem
        logo_url = f"{GITHUB_LOGO_RAW_BASE}{quote(path, safe='/')}"
        for key in [normalized_name(name), without_club_suffix(name)]:
            if key and key not in logos:
                logos[key] = logo_url
    return logos


def github_logo_urls(clubs):
    index = github_logo_index()
    compact_index = {key.replace(" ", ""): value for key, value in index.items()}
    logos = {}
    for link, club_name in clubs.items():
        for candidate in club_name_candidates(club_name, link):
            logo_url = index.get(candidate) or compact_index.get(candidate.replace(" ", ""))
            if logo_url:
                logos[link] = logo_url
                break
    return logos


def wikidata_ids_for_titles(titles_by_link):
    wikidata_ids = {}
    titles = list(dict.fromkeys(titles_by_link.values()))

    for index in range(0, len(titles), 50):
        response = requests.get(
            WIKIPEDIA_API_URL,
            timeout=30,
            headers={"User-Agent": USER_AGENT},
            params={
                "action": "query",
                "format": "json",
                "prop": "pageprops",
                "redirects": "1",
                "titles": "|".join(titles[index : index + 50]),
            },
        )
        if not response.ok:
            continue

        pages = response.json().get("query", {}).get("pages", {})
        qid_by_title = {
            page.get("title", "").replace(" ", "_"): page.get("pageprops", {}).get("wikibase_item", "")
            for page in pages.values()
        }
        for link, title in titles_by_link.items():
            if qid_by_title.get(title):
                wikidata_ids[link] = qid_by_title[title]

    return wikidata_ids


def commons_redirect_url(filename):
    if not filename:
        return ""
    return f"https://commons.wikimedia.org/wiki/Special:Redirect/file/{quote(filename, safe='')}"


def wikidata_logo_urls(club_links):
    titles_by_link = {
        link: wikipedia_title_from_link(link)
        for link in club_links
        if wikipedia_title_from_link(link)
    }
    wikidata_ids = wikidata_ids_for_titles(titles_by_link)
    logos = {}

    qids = list(dict.fromkeys(wikidata_ids.values()))
    for index in range(0, len(qids), 50):
        response = requests.get(
            "https://www.wikidata.org/w/api.php",
            timeout=30,
            headers={"User-Agent": USER_AGENT},
            params={
                "action": "wbgetentities",
                "format": "json",
                "props": "claims",
                "ids": "|".join(qids[index : index + 50]),
            },
        )
        if not response.ok:
            continue

        entities = response.json().get("entities", {})
        logo_by_qid = {}
        fallback_by_qid = {}
        for qid, entity in entities.items():
            claims = entity.get("claims", {})
            logo_claim = (claims.get("P154") or [{}])[0]
            image_claim = (claims.get("P18") or [{}])[0]
            logo_by_qid[qid] = (
                logo_claim.get("mainsnak", {})
                .get("datavalue", {})
                .get("value", "")
            )
            fallback_by_qid[qid] = (
                image_claim.get("mainsnak", {})
                .get("datavalue", {})
                .get("value", "")
            )

        for link, qid in wikidata_ids.items():
            filename = logo_by_qid.get(qid) or fallback_by_qid.get(qid)
            if filename:
                logos[link] = commons_redirect_url(filename)

    return logos


def infobox_logo_for_club(club_link):
    response = requests.get(
        f"https://en.wikipedia.org{club_link}",
        timeout=8,
        headers={"User-Agent": USER_AGENT},
    )
    if not response.ok:
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    infobox = soup.find("table", class_=lambda value: value and "infobox" in value)
    image = infobox.find("img", src=True) if infobox else None
    return absolute_image_url(image["src"]) if image else ""


def sportsdb_logo_for_club(club_name):
    response = requests.get(
        THESPORTSDB_TEAM_SEARCH_URL,
        timeout=10,
        headers={"User-Agent": USER_AGENT},
        params={"t": club_name},
    )
    if not response.ok:
        return ""

    teams = response.json().get("teams") or []
    soccer_teams = [
        team for team in teams
        if normalized_name(team.get("strSport", "")) == "soccer"
    ]
    if not soccer_teams:
        return ""

    club_key = normalized_name(club_name)
    exact_matches = [
        team for team in soccer_teams
        if normalized_name(team.get("strTeam", "")) == club_key
    ]
    return (exact_matches or soccer_teams)[0].get("strBadge", "")


def find_logo_urls(clubs):
    logo_urls = footylogos_logo_urls(clubs)

    missing = [link for link in clubs if not logo_urls.get(link)]
    logo_urls.update(github_logo_urls({link: clubs[link] for link in missing}))

    missing = [link for link in clubs if not logo_urls.get(link)]
    logo_urls.update(wikidata_logo_urls(missing))

    missing = [link for link in clubs if not logo_urls.get(link)]
    logo_urls.update(pageimage_logos(missing))

    missing = [link for link in clubs if not logo_urls.get(link)]
    with ThreadPoolExecutor(max_workers=24) as executor:
        futures = {executor.submit(infobox_logo_for_club, link): link for link in missing}
        for future in as_completed(futures):
            link = futures[future]
            try:
                logo_urls[link] = future.result()
            except requests.RequestException:
                logo_urls[link] = ""

    missing = [link for link in clubs if not logo_urls.get(link)]
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {
            executor.submit(sportsdb_logo_for_club, clubs[link]): link
            for link in missing
        }
        for future in as_completed(futures):
            link = futures[future]
            try:
                logo_urls[link] = future.result()
            except (requests.RequestException, ValueError):
                logo_urls[link] = ""

    return logo_urls


def build_logo_cache(refresh=False):
    clubs = club_links_from_csv() or club_links_from_source_page()
    cache = load_club_logo_cache()
    wanted_links = set(clubs)
    missing_links = {
        link
        for link in wanted_links
        if refresh or link not in cache or not cache.get(link) or not cached_logo_exists(cache[link])
    }

    if not missing_links:
        return clubs, cache, 0

    logo_urls = find_logo_urls({link: clubs[link] for link in missing_links})
    downloaded = 0
    with ThreadPoolExecutor(max_workers=24) as executor:
        futures = {
            executor.submit(cache_logo_image, link, logo_url): link
            for link, logo_url in logo_urls.items()
            if logo_url
        }
        for future in as_completed(futures):
            link = futures[future]
            try:
                cache[link] = future.result()
                downloaded += 1 if cache[link] else 0
            except requests.RequestException:
                cache[link] = ""

    for link in missing_links:
        cache.setdefault(link, "")

    save_club_logo_cache(cache)
    return clubs, cache, downloaded


def main():
    parser = argparse.ArgumentParser(description="Build the local club logo cache.")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-download logos even when a cached file already exists.",
    )
    args = parser.parse_args()

    clubs, cache, downloaded = build_logo_cache(refresh=args.refresh)
    filled = sum(1 for link in clubs if cache.get(link))
    print(f"Found {len(clubs)} clubs.")
    print(f"Cached logos for {filled} clubs.")
    print(f"Downloaded {downloaded} logo files this run.")
    print(f"Wrote {CLUB_LOGO_CACHE} and {CLUB_LOGO_DIR}/")


if __name__ == "__main__":
    main()
