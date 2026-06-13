from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TeamOdds:
    team: str
    group_stage_odds: str = ""
    r16_odds: str = ""
    qf_odds: str = ""
    sf_odds: str = ""
    final_odds: str = ""
    champion_odds: str = ""
    group_stage: float | None = None
    r16: float | None = None
    qf: float | None = None
    sf: float | None = None
    final: float | None = None
    champion: float | None = None
    expected_group_wins: float = 0.0
    expected_group_draws: float = 0.0
    expected_group_goals: float = 0.0


@dataclass
class TeamPrice:
    team: str
    expected_points: float
    price: int | None


GROUP_WIN_POINTS = 3
GROUP_DRAW_POINTS = 1
GOAL_POINTS = 1
ADVANCEMENT_STAGES = {
    "group_stage": 5,
    "r16": 10,
    "qf": 15,
    "sf": 20,
    "final": 25,
    "champion": 40,
}


def american_odds_to_probability(odds: str | int | float | None) -> float | None:
    """Convert American odds to implied probability, without removing sportsbook vig."""
    if odds is None:
        return None

    odds_text = str(odds).strip()
    if odds_text == "":
        return None

    odds_value = float(odds_text.replace("+", ""))
    if odds_value > 0:
        return 100 / (odds_value + 100)
    if odds_value < 0:
        return abs(odds_value) / (abs(odds_value) + 100)

    raise ValueError("American odds cannot be 0.")


def expected_points(team: TeamOdds, include_group_stage: bool = True) -> float:
    total = 0.0

    if include_group_stage:
        total += GROUP_WIN_POINTS * team.expected_group_wins
        total += GROUP_DRAW_POINTS * team.expected_group_draws
        total += GOAL_POINTS * team.expected_group_goals

    for field_name, point_value in ADVANCEMENT_STAGES.items():
        probability = bonus_probability(team, field_name)
        if probability is not None:
            total += point_value * probability

    return total


def stage_probability(team: TeamOdds, field_name: str) -> float | None:
    probability = getattr(team, field_name)
    if probability is not None:
        return probability

    if field_name == "r16":
        return infer_r16_probability(team.group_stage, team.qf)

    return None


def infer_r16_probability(group_stage: float | None, qf: float | None) -> float | None:
    if group_stage is None or qf is None:
        return None

    # Geometric interpolation keeps the estimate between the surrounding stages.
    return (group_stage * qf) ** 0.5


def bonus_probability(team: TeamOdds, field_name: str) -> float | None:
    if field_name != "final":
        return stage_probability(team, field_name)

    final_probability = stage_probability(team, "final")
    champion_probability = stage_probability(team, "champion")
    if final_probability is None:
        return None
    if champion_probability is None:
        return final_probability
    return max(0.0, final_probability - champion_probability)


def calculate_prices(
    teams: list[TeamOdds],
    max_price: int = 75,
    exponent: float = 1.0,
    min_price: int = 1,
    include_group_stage: bool = True,
) -> list[TeamPrice]:
    scored_teams = [
        TeamPrice(team.team, expected_points(team, include_group_stage), 0)
        for team in teams
    ]

    best_expected_points = max(team.expected_points for team in scored_teams)
    if best_expected_points <= 0:
        raise ValueError("At least one team must have positive expected points.")

    priced_teams: list[TeamPrice] = []
    for team in scored_teams:
        if team.expected_points <= 0:
            price = None
        else:
            raw_price = max_price * (team.expected_points / best_expected_points) ** exponent
            price = max(min_price, round(raw_price))

        priced_teams.append(TeamPrice(team.team, team.expected_points, price))

    return sorted(
        priced_teams,
        key=lambda team: (-(team.price or 0), -team.expected_points, team.team),
    )


def load_teams_from_csv(path: Path) -> list[TeamOdds]:
    teams: list[TeamOdds] = []

    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        required_columns = {"team", "qf_odds", "sf_odds", "final_odds", "champion_odds"}
        missing_columns = required_columns - set(reader.fieldnames or [])
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"Missing required CSV columns: {missing}")

        for row in reader:
            team_name = row["team"].strip()
            if not team_name:
                continue

            teams.append(
                TeamOdds(
                    team=team_name,
                    group_stage_odds=clean_text(row.get("group_stage_odds")),
                    r16_odds=clean_text(row.get("r16_odds")),
                    qf_odds=clean_text(row.get("qf_odds")),
                    sf_odds=clean_text(row.get("sf_odds")),
                    final_odds=clean_text(row.get("final_odds")),
                    champion_odds=clean_text(row.get("champion_odds")),
                    group_stage=american_odds_to_probability(row.get("group_stage_odds")),
                    r16=american_odds_to_probability(row.get("r16_odds")),
                    qf=american_odds_to_probability(row.get("qf_odds")),
                    sf=american_odds_to_probability(row.get("sf_odds")),
                    final=american_odds_to_probability(row.get("final_odds")),
                    champion=american_odds_to_probability(row.get("champion_odds")),
                    expected_group_wins=parse_float(row.get("expected_group_wins"), 0.0),
                    expected_group_draws=parse_float(row.get("expected_group_draws"), 0.0),
                    expected_group_goals=parse_float(row.get("expected_group_goals"), 0.0),
                )
            )

    return teams


def parse_float(value: str | None, default: float) -> float:
    if value is None or value.strip() == "":
        return default
    return float(value)


def clean_text(value: str | None) -> str:
    return "" if value is None else value.strip()


def write_prices_to_csv(
    path: Path,
    teams: list[TeamOdds],
    prices: list[TeamPrice],
    include_group_stage: bool = False,
) -> None:
    teams_by_name = {team.team: team for team in teams}
    prices_by_name = {team.team: team for team in prices}
    ordered_names = [team.team for team in prices]
    parts = scoring_parts(include_group_stage)
    fieldnames = ["team", "total_expected_points", "price"]
    for part in parts:
        prefix = part["key"]
        fieldnames.extend(
            [
                f"{prefix}_points_available",
                f"{prefix}_probability",
                f"{prefix}_expected_points",
            ]
        )

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for team_name in ordered_names:
            team = teams_by_name[team_name]
            priced_team = prices_by_name[team_name]
            row = {
                "team": team_name,
                "total_expected_points": format_number(priced_team.expected_points),
                "price": "" if priced_team.price is None else priced_team.price,
            }
            for part in parts:
                prefix = part["key"]
                row[f"{prefix}_points_available"] = part["points_available"]
                row[f"{prefix}_probability"] = part["probability"](team)
                row[f"{prefix}_expected_points"] = part["expected_points"](team)
            writer.writerow(row)


def scoring_parts(include_group_stage: bool) -> list[dict]:
    parts = []
    if include_group_stage:
        parts.extend(
            [
                stat_part("group_wins", GROUP_WIN_POINTS, "expected_group_wins"),
                stat_part("group_draws", GROUP_DRAW_POINTS, "expected_group_draws"),
                stat_part("group_goals", GOAL_POINTS, "expected_group_goals"),
            ]
        )

    for field_name, point_value in ADVANCEMENT_STAGES.items():
        parts.append(stage_part(field_name, point_value))

    return parts


def stat_part(key: str, points_per_unit: int, field_name: str) -> dict:
    return {
        "key": key,
        "points_available": points_per_unit,
        "probability": lambda _team: "",
        "expected_points": lambda team: format_number(
            getattr(team, field_name) * points_per_unit
        ),
    }


def stage_part(field_name: str, point_value: int) -> dict:
    def probability(team: TeamOdds) -> str:
        value = bonus_probability(team, field_name)
        return "" if value is None else format_number(value)

    def expected(team: TeamOdds) -> str:
        value = bonus_probability(team, field_name)
        return "" if value is None else format_number(value * point_value)

    return {
        "key": field_name,
        "points_available": point_value,
        "probability": probability,
        "expected_points": expected,
    }


def step_name(field_name: str) -> str:
    return {
        "r16": "Round of 16 probability",
        "group_stage": "Advance from group probability",
        "qf": "Advance to quarterfinal probability",
        "sf": "Advance to semifinal probability",
        "final": "Runner-up probability",
        "champion": "Win championship probability",
    }[field_name]


def format_number(value: float) -> str:
    return f"{value:.3f}"


def print_prices(prices: list[TeamPrice]) -> None:
    team_width = max(len("Team"), *(len(team.team) for team in prices))
    print(f"{'Team':<{team_width}}  Expected Points  Price")
    print(f"{'-' * team_width}  ---------------  -----")
    for team in prices:
        price = "" if team.price is None else f"${team.price}"
        print(f"{team.team:<{team_width}}  {team.expected_points:>15.3f}  {price:>5}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calculate World Cup salary cap prices from American betting odds."
    )
    parser.add_argument("--input", default="team_odds.csv", help="CSV containing teams and odds.")
    parser.add_argument("--output", default="team_prices.csv", help="CSV file to write prices to.")
    parser.add_argument("--max-price", type=int, default=75, help="Price of the best team.")
    parser.add_argument(
        "--exponent",
        type=float,
        default=1.0,
        help="Power curve exponent. Use 1.0 for straight dollars-per-expected-point pricing.",
    )
    parser.add_argument("--min-price", type=int, default=1, help="Minimum team price.")
    parser.add_argument(
        "--exclude-group-stats",
        action="store_true",
        help="Include expected_group_wins and expected_group_draws in expected points.",
    )
    args = parser.parse_args()

    teams = load_teams_from_csv(Path(args.input))
    prices = calculate_prices(
        teams,
        max_price=args.max_price,
        exponent=args.exponent,
        min_price=args.min_price,
        include_group_stage=not args.exclude_group_stats,
    )

    print_prices(prices)
    write_prices_to_csv(Path(args.output), teams, prices, not args.exclude_group_stats)
    print(f"\nWrote {len(prices)} prices to {args.output}")


if __name__ == "__main__":
    main()
