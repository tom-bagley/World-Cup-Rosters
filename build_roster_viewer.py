import csv
import html
import json
from pathlib import Path


INPUT_CSV = Path("world_cup_rosters.csv")
OUTPUT_HTML = Path("index.html")


def load_rosters():
    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    return [
        {
            "group": row["group"],
            "nationalTeam": row["national_team"],
            "number": row["squad_number"],
            "position": row["position"],
            "player": row["player"],
            "age": row["age"],
            "caps": row["caps"],
            "goals": row["goals"],
            "club": row["professional_club"],
            "clubCountry": row["professional_club_country"],
            "clubLogoUrl": row.get("professional_club_logo_url", ""),
            "fifproApps": row["fifpro_world11_apps"],
            "fifproYears": row["fifpro_world11_years"],
        }
        for row in rows
    ]


def main():
    rosters = load_rosters()
    data_json = json.dumps(rosters, ensure_ascii=False)
    teams = sorted({row["nationalTeam"] for row in rosters})
    team_options = "\n".join(
        f'<option value="{html.escape(team)}">{html.escape(team)}</option>' for team in teams
    )

    OUTPUT_HTML.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>World Cup Rosters</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: Arial, Helvetica, sans-serif;
      background: #f6f7f9;
      color: #172033;
    }}
    body {{
      margin: 0;
      padding: 24px;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
    }}
    header {{
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 18px;
    }}
    h1 {{
      margin: 0 0 4px;
      font-size: 28px;
      line-height: 1.15;
    }}
    .meta {{
      margin: 0;
      color: #667085;
      font-size: 14px;
    }}
    label {{
      display: grid;
      gap: 6px;
      color: #344054;
      font-size: 13px;
      font-weight: 700;
    }}
    select {{
      min-width: 240px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      background: white;
      color: #172033;
      font-size: 15px;
      padding: 9px 36px 9px 10px;
    }}
    .summary {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 14px;
    }}
    .pill {{
      border: 1px solid #d0d7e2;
      border-radius: 999px;
      background: #ffffff;
      padding: 7px 11px;
      color: #344054;
      font-size: 14px;
    }}
    .table-wrap {{
      overflow-x: auto;
      border: 1px solid #d6dde8;
      border-radius: 8px;
      background: white;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 900px;
    }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid #edf0f5;
      text-align: left;
      font-size: 14px;
      white-space: nowrap;
    }}
    th {{
      position: sticky;
      top: 0;
      background: #eef2f7;
      color: #344054;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0;
    }}
    tbody tr:hover {{
      background: #f8fafc;
    }}
    .player {{
      font-weight: 700;
      color: #111827;
    }}
    .club {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }}
    .club-logo {{
      width: 22px;
      height: 22px;
      object-fit: contain;
      flex: 0 0 auto;
    }}
    .muted {{
      color: #667085;
    }}
    @media (max-width: 720px) {{
      body {{
        padding: 16px;
      }}
      header {{
        align-items: stretch;
        flex-direction: column;
      }}
      select {{
        width: 100%;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>World Cup Rosters</h1>
        <p class="meta">Current CSV snapshot with clubs and FIFPRO World 11 selections.</p>
      </div>
      <label>
        Team
        <select id="teamSelect">
          {team_options}
        </select>
      </label>
    </header>

    <section class="summary" id="summary"></section>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>No.</th>
            <th>Pos.</th>
            <th>Player</th>
            <th>Age</th>
            <th>Club</th>
            <th>Club Country</th>
            <th>Caps</th>
            <th>Goals</th>
            <th>FIFPRO Apps</th>
            <th>Years</th>
          </tr>
        </thead>
        <tbody id="rosterBody"></tbody>
      </table>
    </div>
  </main>

  <script>
    const rosters = {data_json};
    const teamSelect = document.getElementById('teamSelect');
    const rosterBody = document.getElementById('rosterBody');
    const summary = document.getElementById('summary');

    function renderTeam(team) {{
      const players = rosters.filter(row => row.nationalTeam === team);
      const totalCaps = players.reduce((sum, row) => sum + Number(row.caps || 0), 0);
      const fifproPlayers = players.filter(row => Number(row.fifproApps || 0) > 0).length;
      const group = players[0]?.group || '';

      summary.innerHTML = [
        ['Group', group],
        ['Players', players.length],
        ['Total caps', totalCaps],
        ['FIFPRO players', fifproPlayers],
      ].map(([label, value]) => `<span class="pill">${{label}}: <strong>${{value}}</strong></span>`).join('');

      rosterBody.innerHTML = players.map(row => `
        <tr>
          <td>${{row.number}}</td>
          <td>${{row.position}}</td>
          <td class="player">${{row.player}}</td>
          <td>${{row.age || '<span class="muted">-</span>'}}</td>
          <td>${{clubMarkup(row)}}</td>
          <td>${{row.clubCountry || '<span class="muted">-</span>'}}</td>
          <td>${{row.caps || '0'}}</td>
          <td>${{row.goals || '0'}}</td>
          <td>${{row.fifproApps || '0'}}</td>
          <td>${{row.fifproYears || '<span class="muted">-</span>'}}</td>
        </tr>
      `).join('');
    }}

    function clubMarkup(row) {{
      if (!row.club) {{
        return '<span class="muted">-</span>';
      }}
      const logo = row.clubLogoUrl
        ? `<img class="club-logo" src="${{row.clubLogoUrl}}" alt="" loading="lazy">`
        : '';
      return `<span class="club">${{logo}}<span>${{row.club}}</span></span>`;
    }}

    teamSelect.addEventListener('change', event => renderTeam(event.target.value));
    renderTeam(teamSelect.value);
  </script>
</body>
</html>
""",
        encoding="utf-8",
    )

    print(f"Wrote {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
