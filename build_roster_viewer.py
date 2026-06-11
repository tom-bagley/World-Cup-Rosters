import csv
import html
import json
import re
import unicodedata
from pathlib import Path


INPUT_CSV = Path("world_cup_rosters.csv")
STARTING_XI_CSV = Path("world_cup_starting_xi.csv")
OUTPUT_HTML = Path("index.html")
TEAM_ALIASES = {
    "czechia": "czech republic",
    "turkiye": "turkey",
    "usa": "united states",
}

TEAM_THEMES = {
    "Algeria": {"flag": "🇩🇿", "primary": "#006233", "secondary": "#d21034"},
    "Argentina": {"flag": "🇦🇷", "primary": "#74acdf", "secondary": "#f6b40e"},
    "Australia": {"flag": "🇦🇺", "primary": "#012169", "secondary": "#e4002b"},
    "Austria": {"flag": "🇦🇹", "primary": "#c8102e", "secondary": "#ffffff"},
    "Belgium": {"flag": "🇧🇪", "primary": "#000000", "secondary": "#fae042"},
    "Bosnia and Herzegovina": {"flag": "🇧🇦", "primary": "#002395", "secondary": "#fecb00"},
    "Brazil": {"flag": "🇧🇷", "primary": "#009739", "secondary": "#ffdf00"},
    "Canada": {"flag": "🇨🇦", "primary": "#d52b1e", "secondary": "#ffffff"},
    "Cape Verde": {"flag": "🇨🇻", "primary": "#003893", "secondary": "#cf2027"},
    "Colombia": {"flag": "🇨🇴", "primary": "#003893", "secondary": "#fcd116"},
    "Croatia": {"flag": "🇭🇷", "primary": "#171796", "secondary": "#ff0000"},
    "Curaçao": {"flag": "🇨🇼", "primary": "#002b7f", "secondary": "#f9e814"},
    "Czech Republic": {"flag": "🇨🇿", "primary": "#11457e", "secondary": "#d7141a"},
    "DR Congo": {"flag": "🇨🇩", "primary": "#007fff", "secondary": "#f7d618"},
    "Ecuador": {"flag": "🇪🇨", "primary": "#034ea2", "secondary": "#ffdd00"},
    "Egypt": {"flag": "🇪🇬", "primary": "#ce1126", "secondary": "#000000"},
    "England": {"flag": "🏴", "primary": "#cf142b", "secondary": "#ffffff"},
    "France": {"flag": "🇫🇷", "primary": "#0055a4", "secondary": "#ef4135"},
    "Germany": {"flag": "🇩🇪", "primary": "#dd0000", "secondary": "#ffce00"},
    "Ghana": {"flag": "🇬🇭", "primary": "#006b3f", "secondary": "#fcd116"},
    "Haiti": {"flag": "🇭🇹", "primary": "#00209f", "secondary": "#d21034"},
    "Iran": {"flag": "🇮🇷", "primary": "#239f40", "secondary": "#da0000"},
    "Iraq": {"flag": "🇮🇶", "primary": "#ce1126", "secondary": "#007a3d"},
    "Ivory Coast": {"flag": "🇨🇮", "primary": "#f77f00", "secondary": "#009e60"},
    "Japan": {"flag": "🇯🇵", "primary": "#bc002d", "secondary": "#ffffff"},
    "Jordan": {"flag": "🇯🇴", "primary": "#007a3d", "secondary": "#ce1126"},
    "Mexico": {"flag": "🇲🇽", "primary": "#006847", "secondary": "#ce1126"},
    "Morocco": {"flag": "🇲🇦", "primary": "#c1272d", "secondary": "#006233"},
    "Netherlands": {"flag": "🇳🇱", "primary": "#21468b", "secondary": "#ae1c28"},
    "New Zealand": {"flag": "🇳🇿", "primary": "#00247d", "secondary": "#cc142b"},
    "Norway": {"flag": "🇳🇴", "primary": "#ba0c2f", "secondary": "#00205b"},
    "Panama": {"flag": "🇵🇦", "primary": "#005293", "secondary": "#d21034"},
    "Paraguay": {"flag": "🇵🇾", "primary": "#0038a8", "secondary": "#d52b1e"},
    "Portugal": {"flag": "🇵🇹", "primary": "#006600", "secondary": "#ff0000"},
    "Qatar": {"flag": "🇶🇦", "primary": "#8a1538", "secondary": "#ffffff"},
    "Saudi Arabia": {"flag": "🇸🇦", "primary": "#006c35", "secondary": "#ffffff"},
    "Scotland": {"flag": "🏴", "primary": "#005eb8", "secondary": "#ffffff"},
    "Senegal": {"flag": "🇸🇳", "primary": "#00853f", "secondary": "#fdef42"},
    "South Africa": {"flag": "🇿🇦", "primary": "#007a4d", "secondary": "#ffb612"},
    "South Korea": {"flag": "🇰🇷", "primary": "#c60c30", "secondary": "#003478"},
    "Spain": {"flag": "🇪🇸", "primary": "#aa151b", "secondary": "#f1bf00"},
    "Sweden": {"flag": "🇸🇪", "primary": "#006aa7", "secondary": "#fecc00"},
    "Switzerland": {"flag": "🇨🇭", "primary": "#ff0000", "secondary": "#ffffff"},
    "Tunisia": {"flag": "🇹🇳", "primary": "#e70013", "secondary": "#ffffff"},
    "Turkey": {"flag": "🇹🇷", "primary": "#e30a17", "secondary": "#ffffff"},
    "United States": {"flag": "🇺🇸", "primary": "#3c3b6e", "secondary": "#b22234"},
    "Uruguay": {"flag": "🇺🇾", "primary": "#0038a8", "secondary": "#fcd116"},
    "Uzbekistan": {"flag": "🇺🇿", "primary": "#1eb53a", "secondary": "#0099b5"},
}


def normalize(value):
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def canonical_team(value):
    key = normalize(value)
    return TEAM_ALIASES.get(key, key)


def load_starting_xi():
    if not STARTING_XI_CSV.exists():
        return {}

    with STARTING_XI_CSV.open("r", encoding="utf-8-sig", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    starters = {}
    for row in rows:
        team = canonical_team(row["team"])
        player = normalize(row["player_name"])
        starter = {
            "starterOrder": int(row["starter_order"]),
            "lineupRole": row["lineup_role"],
            "lineupFormation": row["formation"],
        }
        starters[("number", team, row["shirt_number"])] = starter
        starters[("name", team, player)] = starter

    return starters


def load_rosters():
    starters = load_starting_xi()

    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    rosters = []
    for row in rows:
        team = canonical_team(row["national_team"])
        starter = starters.get(
            ("number", team, row["squad_number"]),
            starters.get(("name", team, normalize(row["player"])), {}),
        )
        rosters.append(
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
            "isStarter": bool(starter),
            "starterOrder": starter.get("starterOrder", 999),
            "lineupRole": starter.get("lineupRole", ""),
            "lineupFormation": starter.get("lineupFormation", ""),
        }
        )

    return rosters


def main():
    rosters = load_rosters()
    data_json = json.dumps(rosters, ensure_ascii=False)
    themes_json = json.dumps(TEAM_THEMES, ensure_ascii=False)
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
      --team-primary: #172033;
      --team-secondary: #d0d7e2;
      --team-primary-soft: rgba(23, 32, 51, 0.08);
      --team-secondary-soft: rgba(208, 215, 226, 0.18);
    }}
    body {{
      margin: 0;
      padding: 24px;
      background:
        linear-gradient(135deg, var(--team-primary-soft), transparent 38%),
        linear-gradient(315deg, var(--team-secondary-soft), transparent 42%),
        #f6f7f9;
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
      border-bottom: 4px solid var(--team-primary);
      padding-bottom: 16px;
    }}
    .title-row {{
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }}
    .team-flag {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 52px;
      height: 40px;
      border: 1px solid #d6dde8;
      border-radius: 6px;
      background: #fff;
      box-shadow: inset 0 -5px 0 var(--team-secondary);
      font-size: 30px;
      line-height: 1;
      flex: 0 0 auto;
    }}
    h1 {{
      margin: 0 0 4px;
      font-size: 28px;
      line-height: 1.15;
      color: var(--team-primary);
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
      border: 1px solid color-mix(in srgb, var(--team-primary), #ffffff 68%);
      border-radius: 999px;
      background: color-mix(in srgb, var(--team-secondary), #ffffff 86%);
      padding: 7px 11px;
      color: #344054;
      font-size: 14px;
    }}
    .table-wrap {{
      overflow-x: auto;
      border: 1px solid color-mix(in srgb, var(--team-primary), #ffffff 72%);
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
      background: var(--team-primary);
      color: #ffffff;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0;
    }}
    tbody tr:hover {{
      background: #f8fafc;
    }}
    tbody tr.starter {{
      background: color-mix(in srgb, var(--team-secondary), #ffffff 82%);
      box-shadow: inset 4px 0 0 var(--team-secondary);
    }}
    tbody tr.starter:hover {{
      background: color-mix(in srgb, var(--team-secondary), #ffffff 74%);
    }}
    .player {{
      font-weight: 700;
      color: #111827;
    }}
    .starter-badge {{
      display: inline-flex;
      align-items: center;
      margin-left: 8px;
      border: 1px solid var(--team-primary);
      border-radius: 999px;
      background: var(--team-primary);
      color: #ffffff;
      padding: 2px 7px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
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
      .team-flag {{
        width: 46px;
        height: 36px;
        font-size: 26px;
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
        <div class="title-row">
          <span class="team-flag" id="teamFlag" aria-hidden="true"></span>
          <div>
            <h1 id="teamTitle">World Cup Rosters</h1>
            <p class="meta">Current CSV snapshot with clubs and FIFPRO World 11 selections.</p>
          </div>
        </div>
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
    const teamThemes = {themes_json};
    const teamSelect = document.getElementById('teamSelect');
    const rosterBody = document.getElementById('rosterBody');
    const summary = document.getElementById('summary');
    const teamTitle = document.getElementById('teamTitle');
    const teamFlag = document.getElementById('teamFlag');

    function renderTeam(team) {{
      applyTeamTheme(team);
      const players = rosters
        .filter(row => row.nationalTeam === team)
        .sort((a, b) => {{
          if (a.isStarter !== b.isStarter) {{
            return a.isStarter ? -1 : 1;
          }}
          if (a.isStarter && b.isStarter) {{
            return Number(a.starterOrder || 999) - Number(b.starterOrder || 999);
          }}
          return Number(a.number || 999) - Number(b.number || 999);
        }});
      const totalCaps = players.reduce((sum, row) => sum + Number(row.caps || 0), 0);
      const fifproPlayers = players.filter(row => Number(row.fifproApps || 0) > 0).length;
      const starterCount = players.filter(row => row.isStarter).length;
      const formation = players.find(row => row.lineupFormation)?.lineupFormation || '-';
      const group = players[0]?.group || '';

      summary.innerHTML = [
        ['Group', group],
        ['Players', players.length],
        ['Projected XI', starterCount],
        ['Formation', formation],
        ['Total caps', totalCaps],
        ['FIFPRO players', fifproPlayers],
      ].map(([label, value]) => `<span class="pill">${{label}}: <strong>${{value}}</strong></span>`).join('');

      rosterBody.innerHTML = players.map(row => `
        <tr class="${{row.isStarter ? 'starter' : ''}}">
          <td>${{row.number}}</td>
          <td>${{row.position}}</td>
          <td class="player">${{row.player}}${{row.isStarter ? `<span class="starter-badge">XI ${{row.lineupRole}}</span>` : ''}}</td>
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

    function applyTeamTheme(team) {{
      const theme = teamThemes[team] || {{
        flag: '🏆',
        primary: '#172033',
        secondary: '#d0d7e2',
      }};
      const root = document.documentElement;
      root.style.setProperty('--team-primary', theme.primary);
      root.style.setProperty('--team-secondary', theme.secondary);
      root.style.setProperty('--team-primary-soft', hexToRgba(theme.primary, 0.10));
      root.style.setProperty('--team-secondary-soft', hexToRgba(theme.secondary, 0.16));
      teamTitle.textContent = `${{team}} Roster`;
      teamFlag.textContent = theme.flag;
      teamFlag.setAttribute('aria-label', `${{team}} flag`);
    }}

    function hexToRgba(hex, alpha) {{
      const value = hex.replace('#', '');
      const red = parseInt(value.slice(0, 2), 16);
      const green = parseInt(value.slice(2, 4), 16);
      const blue = parseInt(value.slice(4, 6), 16);
      return `rgba(${{red}}, ${{green}}, ${{blue}}, ${{alpha}})`;
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
