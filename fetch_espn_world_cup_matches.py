import argparse
import csv
import json
from pathlib import Path

import requests


LEAGUE = "fifa.world"
BASE_URL = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{LEAGUE}"
DEFAULT_DATES = "20260611-20260719"
HEADERS = {"User-Agent": "WorldCupRosters/0.1 (personal research project)"}
OUTPUT_JSON = Path("world_cup_matches.json")
OUTPUT_CSV = Path("world_cup_matches.csv")
OUTPUT_GOALS_CSV = Path("world_cup_goals.csv")
OUTPUT_STARTERS_CSV = Path("world_cup_confirmed_starting_xi.csv")


def get_json(url, params=None):
    response = requests.get(url, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def scoreboard(dates, limit):
    return get_json(f"{BASE_URL}/scoreboard", {"dates": dates, "limit": limit})


def summary(event_id):
    return get_json(f"{BASE_URL}/summary", {"event": event_id})


def compact_competitor(competitor):
    team = competitor.get("team", {})
    return {
        "team_id": team.get("id", ""),
        "team": team.get("displayName", ""),
        "abbreviation": team.get("abbreviation", ""),
        "home_away": competitor.get("homeAway", ""),
        "score": competitor.get("score", ""),
        "winner": competitor.get("winner", False),
    }


def parse_scoreboard_event(event):
    competition = (event.get("competitions") or [{}])[0]
    competitors = [compact_competitor(row) for row in competition.get("competitors", [])]
    status = event.get("status", {}).get("type", {})
    return {
        "event_id": event.get("id", ""),
        "name": event.get("name", ""),
        "short_name": event.get("shortName", ""),
        "date": event.get("date", ""),
        "venue": competition.get("venue", {}).get("fullName", ""),
        "city": competition.get("venue", {}).get("address", {}).get("city", ""),
        "status": status.get("description", ""),
        "status_state": status.get("state", ""),
        "completed": status.get("completed", False),
        "competitors": competitors,
    }


def parse_goals(summary_data):
    goals = []
    for event in summary_data.get("keyEvents", []):
        if not event.get("scoringPlay"):
            continue

        participants = event.get("participants") or []
        scorer = (participants[0].get("athlete", {}) if participants else {})
        assister = (participants[1].get("athlete", {}) if len(participants) > 1 else {})
        goals.append(
            {
                "event_id": summary_data.get("header", {}).get("id", ""),
                "goal_event_id": event.get("id", ""),
                "team": event.get("team", {}).get("displayName", ""),
                "minute": event.get("clock", {}).get("displayValue", ""),
                "period": event.get("period", {}).get("number", ""),
                "type": event.get("type", {}).get("text", ""),
                "scorer": scorer.get("displayName", ""),
                "scorer_id": scorer.get("id", ""),
                "assister": assister.get("displayName", ""),
                "assister_id": assister.get("id", ""),
                "text": event.get("text", ""),
            }
        )
    return goals


def parse_starters(summary_data):
    starters = []
    for team_roster in summary_data.get("rosters", []):
        team = team_roster.get("team", {})
        formation = team_roster.get("formation", "")
        for player in team_roster.get("roster", []):
            if not player.get("starter"):
                continue

            athlete = player.get("athlete", {})
            position = player.get("position", {})
            starters.append(
                {
                    "event_id": summary_data.get("header", {}).get("id", ""),
                    "team_id": team.get("id", ""),
                    "team": team.get("displayName", ""),
                    "abbreviation": team.get("abbreviation", ""),
                    "formation": formation,
                    "shirt_number": player.get("jersey", ""),
                    "player_id": athlete.get("id", ""),
                    "player_name": athlete.get("displayName", ""),
                    "position": position.get("abbreviation", position.get("displayName", "")),
                    "formation_place": player.get("formationPlace", ""),
                }
            )
    return starters


def enrich_match(match):
    summary_data = summary(match["event_id"])
    match["goals"] = parse_goals(summary_data)
    match["starters"] = parse_starters(summary_data)
    return match


def write_csv(path, rows, fieldnames):
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch World Cup match scores, goals, and confirmed lineups from ESPN's public site API."
    )
    parser.add_argument("--dates", default=DEFAULT_DATES, help="ESPN date range, e.g. 20260611-20260719")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument(
        "--summaries",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Fetch each event summary for goals and confirmed starters.",
    )
    args = parser.parse_args()

    events = scoreboard(args.dates, args.limit).get("events", [])
    matches = [parse_scoreboard_event(event) for event in events]
    if args.summaries:
        matches = [enrich_match(match) for match in matches]

    OUTPUT_JSON.write_text(json.dumps(matches, ensure_ascii=False, indent=2), encoding="utf-8")

    match_rows = []
    goal_rows = []
    starter_rows = []
    for match in matches:
        teams = {row["home_away"]: row for row in match["competitors"]}
        home = teams.get("home", {})
        away = teams.get("away", {})
        match_rows.append(
            {
                "event_id": match["event_id"],
                "date": match["date"],
                "status": match["status"],
                "status_state": match["status_state"],
                "completed": match["completed"],
                "home_team": home.get("team", ""),
                "home_score": home.get("score", ""),
                "away_team": away.get("team", ""),
                "away_score": away.get("score", ""),
                "venue": match["venue"],
                "city": match["city"],
            }
        )
        goal_rows.extend(match.get("goals", []))
        starter_rows.extend(match.get("starters", []))

    write_csv(
        OUTPUT_CSV,
        match_rows,
        [
            "event_id",
            "date",
            "status",
            "status_state",
            "completed",
            "home_team",
            "home_score",
            "away_team",
            "away_score",
            "venue",
            "city",
        ],
    )
    write_csv(
        OUTPUT_GOALS_CSV,
        goal_rows,
        [
            "event_id",
            "goal_event_id",
            "team",
            "minute",
            "period",
            "type",
            "scorer",
            "scorer_id",
            "assister",
            "assister_id",
            "text",
        ],
    )
    write_csv(
        OUTPUT_STARTERS_CSV,
        starter_rows,
        [
            "event_id",
            "team_id",
            "team",
            "abbreviation",
            "formation",
            "shirt_number",
            "player_id",
            "player_name",
            "position",
            "formation_place",
        ],
    )

    print(f"Wrote {len(matches)} matches to {OUTPUT_JSON} and {OUTPUT_CSV}")
    print(f"Wrote {len(goal_rows)} goals to {OUTPUT_GOALS_CSV}")
    print(f"Wrote {len(starter_rows)} confirmed starters to {OUTPUT_STARTERS_CSV}")


if __name__ == "__main__":
    main()
