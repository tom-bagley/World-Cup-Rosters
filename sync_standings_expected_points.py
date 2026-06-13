from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


EXPECTED_POINTS_START_MARKER = "    const teamExpectedSeasonPoints = {"
BREAKDOWN_START_MARKER = "    const teamExpectedPointBreakdowns = {"
END_MARKER = "    };"

PARTS = (
    ("group_wins", "Expected wins"),
    ("group_draws", "Expected draws"),
    ("group_goals", "Expected goals"),
    ("group_stage", "Gets out of group stage"),
    ("r16", "Sweet 16"),
    ("qf", "Elite 8"),
    ("sf", "Final 4"),
    ("final", "Runner up"),
    ("champion", "Champion"),
)


def load_price_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        required_columns = {"team", "total_expected_points"}
        missing_columns = required_columns - set(reader.fieldnames or [])
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"Missing required CSV columns: {missing}")

        rows: list[dict[str, str]] = []
        for row in reader:
            if not (row.get("team") or "").strip():
                continue
            rows.append(row)

    return rows


def js_key(value: str) -> str:
    if re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", value):
        return value
    return repr(value)


def expected_points_block(rows: list[dict[str, str]]) -> str:
    lines = [EXPECTED_POINTS_START_MARKER]
    for row in rows:
        team = row["team"].strip()
        points = float(row["total_expected_points"])
        lines.append(f"      {js_key(team)}: {points:.3f},")
    lines.append(END_MARKER)
    return "\n".join(lines)


def breakdown_block(rows: list[dict[str, str]]) -> str:
    lines = [BREAKDOWN_START_MARKER]
    for row in rows:
        team = row["team"].strip()
        total = float(row["total_expected_points"])
        lines.append(f"      {js_key(team)}: {{")
        lines.append(f"        total: {total:.3f},")
        lines.append("        parts: [")
        for prefix, label in PARTS:
            expected = row.get(f"{prefix}_expected_points") or ""
            if expected == "":
                continue
            probability = row.get(f"{prefix}_probability") or ""
            points_available = row.get(f"{prefix}_points_available") or ""
            lines.append(
                "          { "
                + f"label: {repr(label)}, "
                + f"pointsAvailable: {repr(points_available)}, "
                + f"probability: {repr(probability)}, "
                + f"expected: {float(expected):.3f}"
                + " },"
            )
        lines.append("        ],")
        lines.append("      },")
    lines.append(END_MARKER)
    return "\n".join(lines)


def replace_block(html: str, start_marker: str, replacement: str, path: Path) -> str:
    start = html.find(start_marker)
    if start == -1:
        raise ValueError(f"Could not find start marker {start_marker!r} in {path}.")

    end = html.find(END_MARKER, start + len(start_marker))
    if end == -1:
        raise ValueError(f"Could not find block end marker after {start_marker!r} in {path}.")
    end += len(END_MARKER)

    return html[:start] + replacement + html[end:]


def sync_standings(standings_path: Path, prices_path: Path) -> int:
    rows = load_price_rows(prices_path)
    if not rows:
        raise ValueError(f"No expected point rows found in {prices_path}.")

    html = standings_path.read_text(encoding="utf-8")
    updated_html = replace_block(
        html,
        EXPECTED_POINTS_START_MARKER,
        expected_points_block(rows),
        standings_path,
    )
    updated_html = replace_block(
        updated_html,
        BREAKDOWN_START_MARKER,
        breakdown_block(rows),
        standings_path,
    )
    standings_path.write_text(updated_html, encoding="utf-8")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync team expected points from team_prices.csv into standings.html."
    )
    parser.add_argument("--prices", default="team_prices.csv", help="Expected points CSV.")
    parser.add_argument("--standings", default="standings.html", help="Standings HTML file.")
    args = parser.parse_args()

    count = sync_standings(Path(args.standings), Path(args.prices))
    print(f"Synced expected points for {count} teams into {args.standings}.")


if __name__ == "__main__":
    main()
