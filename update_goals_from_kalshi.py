from __future__ import annotations

import csv
import re
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path


INPUT_PATH = Path("team_odds.csv")
OUTPUT_PATH = Path("team_odds.csv")
KALSHI_MARKETS_URL = (
    "https://external-api.kalshi.com/trade-api/v2/markets?"
    + urllib.parse.urlencode({"series_ticker": "KXWCTEAMTOTALGOALS", "limit": "1000"})
)
KALSHI_STAGE_MARKETS_URL = (
    "https://external-api.kalshi.com/trade-api/v2/markets?"
    + urllib.parse.urlencode({"series_ticker": "KXWCSTAGEOFELIM", "limit": "1000"})
)
KALSHI_GAME_MARKETS_URL = (
    "https://external-api.kalshi.com/trade-api/v2/markets?"
    + urllib.parse.urlencode({"series_ticker": "KXWCGAME", "limit": "1000"})
)
ESPN_SCOREBOARD_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?"
    + urllib.parse.urlencode({"limit": "200", "dates": "20260611-20260719"})
)

STAGE_MARKET_CODES = {
    "GS": "group_stage",
    "R32": "r32",
    "R16": "r16_elim",
    "QF": "qf_elim",
    "SF": "sf_elim",
    "FL": "final_loss",
    "FW": "champion",
}

ODDS_FIELDS = (
    "group_stage_odds",
    "r16_odds",
    "qf_odds",
    "sf_odds",
    "final_odds",
    "champion_odds",
)

TEAM_CODE_OVERRIDES = {
    "Algeria": "DZA",
    "Bosnia and Herzegovina": "BIH",
    "Haiti": "HTI",
    "Iran": "IRI",
    "Iraq": "IRQ",
    "Japan": "JPN",
    "Morocco": "MAR",
    "Netherlands": "NED",
    "New Zealand": "NZL",
    "Saudi Arabia": "KSA",
    "South Africa": "RSA",
    "Spain": "ESP",
    "Switzerland": "SUI",
    "Cote d'Ivoire": "CIV",
    "Korea Republic": "KOR",
    "Turkiye": "TUR",
    "DR Congo": "COD",
    "Cape Verde": "CPV",
    "Curacao": "CUW",
    "USA": "USA",
}


def probability_from_market(market: dict) -> float | None:
    bid = parse_price(market.get("yes_bid_dollars"))
    ask = parse_price(market.get("yes_ask_dollars"))
    last = parse_price(market.get("last_price_dollars"))

    if bid is not None and ask is not None and ask > 0:
        return (bid + ask) / 2
    if last is not None and last > 0:
        return last
    if bid is not None:
        return bid
    if ask is not None:
        return ask
    return None


def parse_price(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def team_code(team: str) -> str:
    if team in TEAM_CODE_OVERRIDES:
        return TEAM_CODE_OVERRIDES[team]

    cleaned = re.sub(r"[^A-Za-z]", "", team).upper()
    return cleaned[:3]


def display_team_name(value: str, teams_by_normalized_name: dict[str, str]) -> str:
    normalized = normalize_name(value)
    return teams_by_normalized_name.get(normalized, value)


def normalize_name(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def expected_goals_from_ladder(markets: list[dict]) -> float | None:
    survival_by_threshold: dict[int, float] = {}
    for market in markets:
        threshold = market.get("floor_strike")
        probability = probability_from_market(market)
        if threshold is None or probability is None:
            continue
        survival_by_threshold[int(threshold)] = probability

    if not survival_by_threshold:
        return None

    expected_goals = 0.0
    max_threshold = max(survival_by_threshold)
    last_probability = 1.0

    for threshold in range(1, max_threshold + 1):
        probability = survival_by_threshold.get(threshold)
        if probability is None:
            probability = last_probability
        expected_goals += probability
        last_probability = probability

    return expected_goals


def fetch_kalshi_markets() -> dict[str, list[dict]]:
    with urllib.request.urlopen(KALSHI_MARKETS_URL, timeout=20) as response:
        data = response.read().decode("utf-8")

    import json

    markets = json.loads(data)["markets"]
    by_code: dict[str, list[dict]] = defaultdict(list)
    for market in markets:
        ticker = market.get("ticker", "")
        match = re.match(r"KXWCTEAMTOTALGOALS-26([A-Z]+)-", ticker)
        if match:
            by_code[match.group(1)].append(market)

    return by_code


def fetch_kalshi_stage_markets() -> dict[str, dict[str, float]]:
    with urllib.request.urlopen(KALSHI_STAGE_MARKETS_URL, timeout=20) as response:
        data = response.read().decode("utf-8")

    import json

    by_code: dict[str, dict[str, float]] = defaultdict(dict)
    for market in json.loads(data)["markets"]:
        ticker = market.get("ticker", "")
        match = re.match(r"KXWCSTAGEOFELIM-26([A-Z]+)-([A-Z0-9]+)$", ticker)
        if not match:
            continue

        code, stage_code = match.groups()
        stage_name = STAGE_MARKET_CODES.get(stage_code)
        probability = probability_from_market(market)
        if stage_name and probability is not None:
            by_code[code][stage_name] = probability

    return by_code


def fetch_kalshi_game_markets() -> dict[str, dict[str, float]]:
    with urllib.request.urlopen(KALSHI_GAME_MARKETS_URL, timeout=20) as response:
        data = response.read().decode("utf-8")

    import json

    markets_by_game: dict[str, dict[str, float]] = defaultdict(dict)
    for market in json.loads(data)["markets"]:
        if market.get("status") != "active":
            continue

        ticker = market.get("ticker", "")
        match = re.match(r"(KXWCGAME-26[A-Z0-9]+)-([A-Z]+)$", ticker)
        probability = probability_from_market(market)
        if not match or probability is None:
            continue

        game_ticker, outcome_code = match.groups()
        markets_by_game[game_ticker][outcome_code] = probability

    return markets_by_game


def fetch_actual_group_stats(teams_by_normalized_name: dict[str, str]) -> dict[str, dict[str, float]]:
    with urllib.request.urlopen(ESPN_SCOREBOARD_URL, timeout=20) as response:
        data = response.read().decode("utf-8")

    import json

    stats: dict[str, dict[str, float]] = defaultdict(lambda: {"wins": 0.0, "draws": 0.0, "goals": 0.0})
    for event in json.loads(data).get("events", []):
        competition = (event.get("competitions") or [{}])[0]
        competitors = competition.get("competitors") or []
        status = ((event.get("status") or {}).get("type") or {})
        if status.get("state") != "post" or len(competitors) < 2:
            continue

        first, second = competitors[:2]
        first_name = display_team_name(
            ((first.get("team") or {}).get("displayName") or ""),
            teams_by_normalized_name,
        )
        second_name = display_team_name(
            ((second.get("team") or {}).get("displayName") or ""),
            teams_by_normalized_name,
        )
        if first_name not in teams_by_normalized_name.values() or second_name not in teams_by_normalized_name.values():
            continue

        first_score = int(first.get("score") or 0)
        second_score = int(second.get("score") or 0)
        stats[first_name]["goals"] += first_score
        stats[second_name]["goals"] += second_score
        if first_score > second_score:
            stats[first_name]["wins"] += 1.0
        elif second_score > first_score:
            stats[second_name]["wins"] += 1.0
        else:
            stats[first_name]["draws"] += 1.0
            stats[second_name]["draws"] += 1.0

    return stats


def expected_group_results_from_games(
    rows: list[dict[str, str]],
    game_markets: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    rows_by_code = {team_code(row["team"]): row for row in rows}
    group_by_team = {row["team"]: row.get("group", "") for row in rows}
    expected = {
        row["team"]: {
            "wins": 0.0,
            "draws": 0.0,
        }
        for row in rows
    }

    for outcomes in game_markets.values():
        team_codes = [code for code in outcomes if code != "TIE" and code in rows_by_code]
        if len(team_codes) != 2 or "TIE" not in outcomes:
            continue

        first_team = rows_by_code[team_codes[0]]["team"]
        second_team = rows_by_code[team_codes[1]]["team"]
        if group_by_team[first_team] == "" or group_by_team[first_team] != group_by_team[second_team]:
            continue

        total_probability = sum(outcomes[code] for code in [*team_codes, "TIE"])
        if total_probability <= 0:
            continue

        for code in team_codes:
            expected[rows_by_code[code]["team"]]["wins"] += outcomes[code] / total_probability

        draw_probability = outcomes["TIE"] / total_probability
        expected[first_team]["draws"] += draw_probability
        expected[second_team]["draws"] += draw_probability

    return expected


def reach_probabilities(stage_probabilities: dict[str, float]) -> dict[str, float] | None:
    required = set(STAGE_MARKET_CODES.values())
    if not required.issubset(stage_probabilities):
        return None

    normalized = normalize_stage_probabilities(stage_probabilities)
    champion = normalized["champion"]
    final_loss = normalized["final_loss"]
    sf_elim = normalized["sf_elim"]
    qf_elim = normalized["qf_elim"]
    r16_elim = normalized["r16_elim"]
    r32_elim = normalized["r32"]

    return {
        "group_stage_odds": 1 - normalized["group_stage"],
        "r16_odds": r16_elim + qf_elim + sf_elim + final_loss + champion,
        "qf_odds": qf_elim + sf_elim + final_loss + champion,
        "sf_odds": sf_elim + final_loss + champion,
        "final_odds": final_loss + champion,
        "champion_odds": champion,
    }


def normalize_stage_probabilities(stage_probabilities: dict[str, float]) -> dict[str, float]:
    total = sum(stage_probabilities.values())
    if total <= 0:
        return stage_probabilities
    return {
        stage: max(0.0, min(1.0, probability / total))
        for stage, probability in stage_probabilities.items()
    }


def probability_to_american_odds(probability: float) -> str:
    probability = max(0.001, min(0.999, probability))
    if probability >= 0.5:
        odds = -round((probability / (1 - probability)) * 100)
    else:
        odds = round(((1 - probability) / probability) * 100)
    return f"{odds:+d}" if odds > 0 else str(odds)


def main() -> None:
    with INPUT_PATH.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    for fieldname in ("expected_group_goals", "expected_group_goals_source"):
        if fieldname not in fieldnames:
            fieldnames.append(fieldname)
    for fieldname in ("expected_group_wins_source", "expected_group_draws_source"):
        if fieldname not in fieldnames:
            fieldnames.append(fieldname)
    if "stage_odds_source" not in fieldnames:
        fieldnames.append("stage_odds_source")

    teams_by_normalized_name = {
        normalize_name(row["team"]): row["team"]
        for row in rows
    }
    kalshi_markets = fetch_kalshi_markets()
    kalshi_stage_markets = fetch_kalshi_stage_markets()
    kalshi_game_markets = fetch_kalshi_game_markets()
    actual_group_stats = fetch_actual_group_stats(teams_by_normalized_name)
    expected_group_results = expected_group_results_from_games(
        rows,
        kalshi_game_markets,
    )
    goals_updated = 0
    group_results_updated = 0
    stage_odds_updated = 0

    for row in rows:
        code = team_code(row["team"])
        group_results = expected_group_results.get(row["team"])
        if group_results:
            row["expected_group_wins"] = f"{group_results['wins']:.3f}"
            row["expected_group_draws"] = f"{group_results['draws']:.3f}"
            row["expected_group_wins_source"] = "kalshi_remaining_games"
            row["expected_group_draws_source"] = "kalshi_remaining_games"
            group_results_updated += 1

        expected_tournament_goals = expected_goals_from_ladder(kalshi_markets.get(code, []))
        if expected_tournament_goals is None:
            row["expected_group_goals_source"] = row.get("expected_group_goals_source") or "model"
        else:
            actual_goals = actual_group_stats[row["team"]]["goals"]
            row["expected_group_goals"] = f"{max(0.0, expected_tournament_goals - actual_goals):.3f}"
            row["expected_group_goals_source"] = "kalshi_tournament_goals_minus_espn_actuals"
            goals_updated += 1

        stages = reach_probabilities(kalshi_stage_markets.get(code, {}))
        if stages is None:
            row["stage_odds_source"] = row.get("stage_odds_source") or "manual"
            continue

        for fieldname in ODDS_FIELDS:
            row[fieldname] = probability_to_american_odds(stages[fieldname])
        row["stage_odds_source"] = "kalshi_stage_of_elimination"
        stage_odds_updated += 1

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated expected_group_goals from Kalshi full-tournament goals for {goals_updated} teams.")
    print(f"Updated expected_group_wins/draws from Kalshi remaining game markets for {group_results_updated} teams.")
    print(f"Updated stage odds from Kalshi stage-of-elimination markets for {stage_odds_updated} teams.")


if __name__ == "__main__":
    main()
