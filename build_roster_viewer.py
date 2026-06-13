import csv
import html
import json
from pathlib import Path


INPUT_CSV = Path("world_cup_rosters.csv")
OUTPUT_HTML = Path("index.html")

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


TEAM_FLAG_CODES = {
    "Algeria": "dz",
    "Argentina": "ar",
    "Australia": "au",
    "Austria": "at",
    "Belgium": "be",
    "Bosnia and Herzegovina": "ba",
    "Brazil": "br",
    "Canada": "ca",
    "Cape Verde": "cv",
    "Colombia": "co",
    "Croatia": "hr",
    "CuraÃ§ao": "cw",
    "Curaçao": "cw",
    "Czech Republic": "cz",
    "DR Congo": "cd",
    "Ecuador": "ec",
    "Egypt": "eg",
    "England": "gb-eng",
    "France": "fr",
    "Germany": "de",
    "Ghana": "gh",
    "Haiti": "ht",
    "Iran": "ir",
    "Iraq": "iq",
    "Ivory Coast": "ci",
    "Japan": "jp",
    "Jordan": "jo",
    "Mexico": "mx",
    "Morocco": "ma",
    "Netherlands": "nl",
    "New Zealand": "nz",
    "Norway": "no",
    "Panama": "pa",
    "Paraguay": "py",
    "Portugal": "pt",
    "Qatar": "qa",
    "Saudi Arabia": "sa",
    "Scotland": "gb-sct",
    "Senegal": "sn",
    "South Africa": "za",
    "South Korea": "kr",
    "Spain": "es",
    "Sweden": "se",
    "Switzerland": "ch",
    "Tunisia": "tn",
    "Turkey": "tr",
    "United States": "us",
    "Uruguay": "uy",
    "Uzbekistan": "uz",
}


def load_rosters():
    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    rosters = []
    for row in rows:
        rosters.append(
            {
            "group": row["group"],
            "nationalTeam": row["national_team"],
            "number": row["squad_number"],
            "position": row["position"],
            "player": row["player"],
            "playerUrl": row.get("player_wikipedia_url", ""),
            "age": row["age"],
            "caps": row["caps"],
            "goals": row["goals"],
            "club": row["professional_club"],
            "clubUrl": row.get("professional_club_wikipedia_url", ""),
            "clubCountry": row["professional_club_country"],
            "clubLogoUrl": row.get("professional_club_logo_url", ""),
            "fifproApps": row["fifpro_world11_apps"],
            "fifproYears": row["fifpro_world11_years"],
            "isStarter": False,
            "starterOrder": 999,
            "lineupRole": "",
            "lineupFormation": "",
        }
        )

    return rosters


def main():
    rosters = load_rosters()
    data_json = json.dumps(rosters, ensure_ascii=False)
    themes = {
        team: {**theme, "flagCode": TEAM_FLAG_CODES.get(team, "")}
        for team, theme in TEAM_THEMES.items()
    }
    themes_json = json.dumps(themes, ensure_ascii=False)
    teams_by_group = {}
    for row in rosters:
        teams_by_group.setdefault(row["group"], set()).add(row["nationalTeam"])
    team_options = "\n".join(
        "\n".join(
            [
                f'<optgroup label="Group {html.escape(group)}">',
                *[
                    f'<option value="{html.escape(team)}">{html.escape(team)}</option>'
                    for team in sorted(teams)
                ],
                "</optgroup>",
            ]
        )
        for group, teams in sorted(teams_by_group.items())
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
      --team-accent: #ffffff;
      --team-page: #101828;
      --team-page-2: #25324a;
      --team-on-page: #111827;
      --team-on-primary: #ffffff;
      --team-on-secondary: #111827;
      --team-primary-soft: rgba(23, 32, 51, 0.28);
      --team-secondary-soft: rgba(208, 215, 226, 0.32);
    }}
    body {{
      margin: 0;
      padding: 24px;
      background:
        linear-gradient(145deg, var(--team-secondary), var(--team-secondary));
      color: #111827;
      min-height: 100vh;
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
      border-bottom: 4px solid color-mix(in srgb, var(--team-primary), #000000 28%);
      padding: 24px;
      border-radius: 8px;
      background: var(--team-primary);
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.22);
    }}
    .title-row {{
      display: flex;
      align-items: center;
      gap: 18px;
      min-width: 0;
    }}
    .team-flag {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 92px;
      height: 60px;
      border: 1px solid rgba(17, 24, 39, 0.62);
      border-radius: 4px;
      background:
        linear-gradient(90deg, var(--team-primary) 0 34%, var(--team-secondary) 34% 67%, var(--team-accent) 67% 100%);
      background-position: center;
      background-size: cover;
      box-shadow: 0 8px 18px rgba(0, 0, 0, 0.24);
      flex: 0 0 auto;
    }}
    h1 {{
      margin: 0 0 4px;
      font-size: 44px;
      line-height: 1.15;
      color: var(--team-on-primary);
    }}
    .meta {{
      margin: 0;
      color: var(--team-on-primary);
      font-size: 14px;
    }}
    label {{
      display: grid;
      gap: 6px;
      color: var(--team-on-primary);
      font-size: 13px;
      font-weight: 700;
      background: var(--team-primary);
      border: 1px solid color-mix(in srgb, var(--team-primary), #000000 42%);
      border-radius: 6px;
      padding: 10px;
    }}
    select {{
      min-width: 240px;
      border: 1px solid color-mix(in srgb, var(--team-primary), #000000 55%);
      border-radius: 6px;
      background: var(--team-primary);
      color: var(--team-on-primary);
      font-size: 15px;
      padding: 9px 36px 9px 10px;
      box-shadow: inset 0 0 0 1px rgba(17, 24, 39, 0.2);
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
      background: var(--team-primary);
      padding: 7px 11px;
      color: var(--team-on-primary);
      font-size: 14px;
      box-shadow: 0 10px 24px rgba(0, 0, 0, 0.14);
    }}
    .table-wrap {{
      overflow-x: auto;
      border: 1px solid color-mix(in srgb, var(--team-primary), #ffffff 72%);
      border-radius: 8px;
      background: white;
      box-shadow: 0 18px 46px rgba(0, 0, 0, 0.24);
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
    tbody td {{
      color: #111827;
    }}
    th {{
      position: sticky;
      top: 0;
      background: var(--team-primary);
      color: var(--team-on-primary);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0;
    }}
    tbody tr:hover {{
      background: #f8fafc;
    }}
    tbody tr.starter {{
      background: color-mix(in srgb, var(--team-primary), #ffffff 82%);
      box-shadow: inset 4px 0 0 var(--team-primary);
    }}
    tbody tr.starter:hover {{
      background: color-mix(in srgb, var(--team-primary), #ffffff 74%);
    }}
    .player {{
      font-weight: 700;
      color: #111827;
    }}
    a.wikilink {{
      color: inherit;
      text-decoration: none;
      border-bottom: 1px solid color-mix(in srgb, currentColor, transparent 65%);
    }}
    a.wikilink:hover {{
      color: var(--team-primary);
      border-bottom-color: currentColor;
    }}
    .starter-badge {{
      display: inline-flex;
      align-items: center;
      margin-left: 8px;
      border: 1px solid var(--team-primary);
      border-radius: 999px;
      background: var(--team-primary);
      color: var(--team-on-primary);
      padding: 2px 7px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
    }}
    .fifpro-star {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      margin-left: 7px;
      color: #d9a441;
      font-size: 15px;
      line-height: 1;
      text-shadow: 0 1px 0 rgba(17, 24, 39, 0.18);
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
    .match-panel {{
      display: grid;
      gap: 10px;
      margin-bottom: 14px;
    }}
    .match-list {{
      display: grid;
      gap: 8px;
    }}
    .match-card {{
      display: grid;
      grid-template-columns: minmax(110px, 1fr) auto minmax(110px, 1fr);
      align-items: center;
      gap: 10px;
      border: 1px solid color-mix(in srgb, var(--team-primary), #ffffff 72%);
      border-radius: 8px;
      background: #ffffff;
      padding: 10px 12px;
      box-shadow: 0 10px 24px rgba(0, 0, 0, 0.14);
    }}
    .match-team {{
      min-width: 0;
      font-weight: 700;
    }}
    .match-team.away {{
      text-align: right;
    }}
    .match-side {{
      display: grid;
      gap: 6px;
      min-width: 0;
      align-self: start;
    }}
    .match-side.away {{
      text-align: right;
    }}
    .match-score {{
      min-width: 72px;
      border-radius: 6px;
      background: var(--team-primary);
      color: var(--team-on-primary);
      padding: 6px 10px;
      text-align: center;
      font-weight: 800;
    }}
    .match-meta {{
      grid-column: 1 / -1;
      display: flex;
      flex-wrap: wrap;
      gap: 6px 12px;
      color: #667085;
      font-size: 12px;
    }}
    .goal-list {{
      margin: 0;
      padding: 0;
      list-style: none;
      color: #344054;
      font-size: 13px;
      font-weight: 400;
      white-space: normal;
    }}
    .goal-list li {{
      padding-top: 4px;
    }}
    @media (max-width: 720px) {{
      body {{
        padding: 10px;
      }}
      header {{
        align-items: stretch;
        flex-direction: column;
        background: var(--team-primary);
        gap: 12px;
        margin-bottom: 10px;
        padding: 14px;
      }}
      .title-row {{
        gap: 10px;
      }}
      .team-flag {{
        width: 54px;
        height: 36px;
      }}
      h1 {{
        font-size: 24px;
      }}
      label {{
        padding: 8px;
      }}
      select {{
        min-width: 0;
        width: 100%;
        font-size: 14px;
        padding-block: 8px;
      }}
      .summary {{
        gap: 6px;
        margin-bottom: 8px;
      }}
      .pill {{
        padding: 5px 8px;
        font-size: 12px;
      }}
      .table-wrap {{
        border-radius: 6px;
      }}
      table {{
        min-width: 0;
      }}
      th, td {{
        padding: 8px 6px;
        font-size: 12px;
      }}
      th {{
        font-size: 10px;
      }}
      th:nth-child(6),
      td:nth-child(6) {{
        display: none;
      }}
      th:nth-child(1),
      td:nth-child(1),
      th:nth-child(2),
      td:nth-child(2),
      th:nth-child(4),
      td:nth-child(4),
      th:nth-child(7),
      td:nth-child(7),
      th:nth-child(8),
      td:nth-child(8) {{
        text-align: center;
      }}
      th:nth-child(3),
      td:nth-child(3) {{
        min-width: 118px;
        white-space: normal;
      }}
      th:nth-child(5),
      td:nth-child(5) {{
        min-width: 104px;
        white-space: normal;
      }}
      .club {{
        gap: 5px;
      }}
      .club-logo {{
        width: 18px;
        height: 18px;
      }}
      .starter-badge {{
        margin-left: 4px;
        padding: 1px 5px;
        font-size: 9px;
      }}
      .match-card {{
        grid-template-columns: minmax(72px, 1fr) auto minmax(72px, 1fr);
        gap: 6px;
        padding: 8px;
      }}
      .match-score {{
        min-width: 54px;
        padding: 5px 7px;
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
    <section class="match-panel" id="matchPanel"></section>

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
    const matchPanel = document.getElementById('matchPanel');
    const ESPN_SCOREBOARD_URL = 'https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?limit=200&dates=20260611-20260719';
    const ESPN_SUMMARY_URL = 'https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/summary?event=';
    const teamAliases = {{
      'Bosnia and Herzegovina': ['Bosnia-Herzegovina'],
      'Czech Republic': ['Czechia'],
      'South Korea': ['Korea Republic'],
      'United States': ['USA'],
    }};
    let espnMatches = [];
    const eventSummaryCache = new Map();

    function renderTeam(team) {{
      applyTeamTheme(team);
      const liveStarters = confirmedStartersForTeam(team);
      const players = rosters
        .filter(row => row.nationalTeam === team)
        .map(row => mergeLiveStarter(row, liveStarters))
        .sort((a, b) => {{
          if (a.isStarter !== b.isStarter) {{
            return a.isStarter ? -1 : 1;
          }}
          if (a.isStarter && b.isStarter) {{
            const roleSort = lineupSortValue(a) - lineupSortValue(b);
            if (roleSort !== 0) {{
              return roleSort;
            }}
            return Number(a.starterOrder || 999) - Number(b.starterOrder || 999);
          }}
          return Number(a.number || 999) - Number(b.number || 999);
      }});
      const totalCaps = players.reduce((sum, row) => sum + Number(row.caps || 0), 0);
      const formation = liveStarters.formation || players.find(row => row.lineupFormation)?.lineupFormation || '-';
      const group = players[0]?.group || '';

      summary.innerHTML = [
        ['Group', group],
        ['Players', players.length],
        ['Formation', formation],
        ['Total caps', totalCaps],
      ].map(([label, value]) => `<span class="pill">${{label}}: <strong>${{value}}</strong></span>`).join('');

      rosterBody.innerHTML = players.map(row => `
        <tr class="${{row.isStarter ? 'starter' : ''}}">
          <td>${{row.number}}</td>
          <td>${{row.position}}</td>
          <td class="player">${{playerMarkup(row)}}${{fifproStarMarkup(row)}}${{row.isStarter ? `<span class="starter-badge">${{escapeHtml(row.lineupRole)}}</span>` : ''}}</td>
          <td>${{row.age || '<span class="muted">-</span>'}}</td>
          <td>${{clubMarkup(row)}}</td>
          <td>${{row.clubCountry || '<span class="muted">-</span>'}}</td>
          <td>${{row.caps || '0'}}</td>
          <td>${{row.goals || '0'}}</td>
        </tr>
      `).join('');
      renderMatches(team);
    }}

    function mergeLiveStarter(row, liveStarters) {{
      const starter = liveStarters.byNumber.get(String(row.number)) || liveStarters.byName.get(normalize(row.player));
      if (!starter) {{
        return liveStarters.hasConfirmedLineup
          ? {{
              ...row,
              isStarter: false,
              starterOrder: 999,
              lineupRole: '',
              lineupFormation: liveStarters.formation || row.lineupFormation,
            }}
          : row;
      }}
      return {{
        ...row,
        isStarter: true,
        starterOrder: Number(starter.formationPlace || row.starterOrder || 999),
        lineupRole: starter.position || row.lineupRole || 'XI',
        lineupFormation: liveStarters.formation || row.lineupFormation,
      }};
    }}

    function lineupSortValue(row) {{
      const role = normalize(row.lineupRole);
      const rawRole = String(row.lineupRole || '').toUpperCase();
      const rosterPosition = normalize(row.position);
      if (role === 'g' || role === 'gk' || role.includes('goalkeeper')) {{
        return 0;
      }}
      if (
        role.includes('cb') ||
        role.includes('cd') ||
        role.includes('lb') ||
        role.includes('rb') ||
        role.includes('def') ||
        (rosterPosition === 'df' && !role)
      ) {{
        return 100 + horizontalSortValue(rawRole);
      }}
      if (role.includes('dm')) {{
        return 200 + horizontalSortValue(rawRole);
      }}
      if (
        role.includes('cm') ||
        role.includes('lm') ||
        role.includes('rm') ||
        role.includes('mid')
      ) {{
        return 300 + horizontalSortValue(rawRole);
      }}
      if (role.includes('am') || role.includes('cf')) {{
        return 400 + horizontalSortValue(rawRole);
      }}
      if (
        role === 'f' ||
        (rosterPosition === 'fw' && !role) ||
        role.includes('fw') ||
        role.includes('st') ||
        role.includes('att') ||
        role.includes('wing')
      ) {{
        return 500 + horizontalSortValue(rawRole);
      }}
      return 600;
    }}

    function horizontalSortValue(role) {{
      if (role.includes('CD-L') || role.includes('CB-L') || role.includes('CM-L')) {{
        return 10;
      }}
      if (role.includes('CD-R') || role.includes('CB-R') || role.includes('CM-R')) {{
        return 30;
      }}
      if (role.includes('-L') || role.endsWith('L') || role.includes('LB') || role.includes('LM')) {{
        return 0;
      }}
      if (role.includes('-R') || role.endsWith('R') || role.includes('RB') || role.includes('RM')) {{
        return 40;
      }}
      return 20;
    }}

    function confirmedStartersForTeam(team) {{
      const lineups = [];
      for (const match of teamMatches(team)) {{
        const summaryData = eventSummaryCache.get(match.id);
        for (const teamRoster of summaryData?.rosters || []) {{
          if (!sameTeam(teamRoster.team?.displayName, team)) {{
            continue;
          }}
          const starters = (teamRoster.roster || []).filter(player => player.starter);
          if (starters.length >= 11) {{
            lineups.push({{
              match,
              formation: teamRoster.formation || '',
              starters: starters.slice(0, 11),
            }});
          }}
        }}
      }}

      const lineup = lineups
        .sort((left, right) => new Date(right.match.date || 0) - new Date(left.match.date || 0))[0];
      const byNumber = new Map();
      const byName = new Map();
      if (!lineup) {{
        return {{ byNumber, byName, formation: '', hasConfirmedLineup: false }};
      }}

      for (const player of lineup.starters) {{
        const starter = {{
          shirtNumber: player.jersey,
          playerName: player.athlete?.displayName || '',
          position: player.position?.abbreviation || player.position?.displayName || '',
          formationPlace: player.formationPlace || '',
        }};
        byNumber.set(String(starter.shirtNumber), starter);
        byName.set(normalize(starter.playerName), starter);
      }}

      return {{
        byNumber,
        byName,
        formation: lineup.formation,
        hasConfirmedLineup: byNumber.size >= 11 || byName.size >= 11,
      }};
    }}

    function renderMatches(team) {{
      if (!espnMatches.length) {{
        matchPanel.innerHTML = '<span class="pill">Loading latest ESPN scores...</span>';
        return;
      }}
      const matches = teamMatches(team);
      if (!matches.length) {{
        matchPanel.innerHTML = '<span class="pill">No ESPN matches found for this team.</span>';
        return;
      }}
      matchPanel.innerHTML = `<div class="match-list">${{matches.map(match => matchMarkup(match, team)).join('')}}</div>`;
      fetchMissingSummaries(matches);
    }}

    function matchMarkup(match, selectedTeam) {{
      const competition = match.competitions?.[0] || {{}};
      const teams = competition.competitors || [];
      const home = teams.find(row => row.homeAway === 'home') || teams[0] || {{}};
      const away = teams.find(row => row.homeAway === 'away') || teams[1] || {{}};
      const selected = teams.find(row => sameTeam(row.team?.displayName, selectedTeam)) || home;
      const opponent = teams.find(row => row !== selected) || away;
      const status = match.status?.type || {{}};
      const venue = competition.venue?.fullName || '';
      const goals = goalsForMatch(match.id);
      const selectedGoals = goals.filter(goal => sameTeam(goal.team, selected.team?.displayName || ''));
      const opponentGoals = goals.filter(goal => sameTeam(goal.team, opponent.team?.displayName || ''));
      const scoreText = status.state === 'pre'
        ? ''
        : `${{selected.score ?? '0'}}-${{opponent.score ?? '0'}}`;
      const scoreMarkup = scoreText
        ? `<div class="match-score">${{escapeHtml(scoreText)}}</div>`
        : '<div></div>';
      return `
        <article class="match-card">
          <div class="match-side home">
            <div class="match-team">${{escapeHtml(selected.team?.displayName || '')}}</div>
            ${{goalListMarkup(selectedGoals)}}
          </div>
          ${{scoreMarkup}}
          <div class="match-side away">
            <div class="match-team">${{escapeHtml(opponent.team?.displayName || '')}}</div>
            ${{goalListMarkup(opponentGoals)}}
          </div>
          <div class="match-meta">
            <span>${{escapeHtml(status.detail || status.shortDetail || status.description || '')}}</span>
            <span>${{escapeHtml(formatMatchDate(match.date))}}</span>
            <span>${{escapeHtml(venue)}}</span>
          </div>
        </article>
      `;
    }}

    function goalListMarkup(goals) {{
      if (!goals.length) {{
        return '';
      }}
      return `<ul class="goal-list">${{goals.map(goal => `<li>${{escapeHtml(goal.minute)}} ${{escapeHtml(goal.scorer)}}${{goal.assister ? `, ast. ${{escapeHtml(goal.assister)}}` : ''}}</li>`).join('')}}</ul>`;
    }}

    function goalsForMatch(eventId) {{
      const summaryData = eventSummaryCache.get(eventId);
      return (summaryData?.keyEvents || [])
        .filter(event => event.scoringPlay)
        .map(event => {{
          const participants = event.participants || [];
          return {{
            minute: event.clock?.displayValue || '',
            team: event.team?.displayName || '',
            scorer: participants[0]?.athlete?.displayName || event.shortText || 'Goal',
            assister: participants[1]?.athlete?.displayName || '',
          }};
        }});
    }}

    function teamMatches(team) {{
      return espnMatches.filter(match => (match.competitions?.[0]?.competitors || [])
        .some(competitor => sameTeam(competitor.team?.displayName, team)));
    }}

    function sameTeam(left, right) {{
      const normalizedLeft = normalize(left);
      const candidates = [right, ...(teamAliases[right] || [])].map(normalize);
      return candidates.includes(normalizedLeft);
    }}

    function normalize(value) {{
      return String(value || '')
        .normalize('NFD')
        .replace(/[\\u0300-\\u036f]/g, '')
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, ' ')
        .trim();
    }}

    async function fetchScoreboard() {{
      try {{
        const response = await fetch(ESPN_SCOREBOARD_URL, {{ cache: 'no-store' }});
        if (!response.ok) {{
          throw new Error(`ESPN scoreboard returned ${{response.status}}`);
        }}
        const data = await response.json();
        espnMatches = data.events || [];
        renderTeam(teamSelect.value);
      }} catch (error) {{
        console.warn(error);
        matchPanel.innerHTML = '<span class="pill">ESPN match data unavailable.</span>';
      }}
    }}

    async function fetchMissingSummaries(matches) {{
      const missing = matches.filter(match => !eventSummaryCache.has(match.id));
      await Promise.all(missing.map(async match => {{
        try {{
          const response = await fetch(`${{ESPN_SUMMARY_URL}}${{encodeURIComponent(match.id)}}`, {{ cache: 'no-store' }});
          if (!response.ok) {{
            throw new Error(`ESPN summary returned ${{response.status}}`);
          }}
          eventSummaryCache.set(match.id, await response.json());
        }} catch (error) {{
          console.warn(error);
          eventSummaryCache.set(match.id, {{ error: true }});
        }}
      }}));
      if (teamMatches(teamSelect.value).some(match => missing.includes(match))) {{
        renderTeam(teamSelect.value);
      }}
    }}

    function formatMatchDate(value) {{
      if (!value) {{
        return '';
      }}
      return new Intl.DateTimeFormat(undefined, {{
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      }}).format(new Date(value));
    }}

    function applyTeamTheme(team) {{
      const theme = teamThemes[team] || {{
        flag: '🏆',
        primary: '#172033',
        secondary: '#d0d7e2',
        accent: '#ffffff',
      }};
      const accent = theme.accent || '#ffffff';
      const root = document.documentElement;
      root.style.setProperty('--team-primary', theme.primary);
      root.style.setProperty('--team-secondary', theme.secondary);
      root.style.setProperty('--team-accent', accent);
      root.style.setProperty('--team-page', theme.secondary);
      root.style.setProperty('--team-page-2', theme.secondary);
      root.style.setProperty('--team-on-page', '#111827');
      root.style.setProperty('--team-on-primary', readableText(theme.primary));
      root.style.setProperty('--team-on-secondary', '#111827');
      root.style.setProperty('--team-primary-soft', hexToRgba(theme.primary, 0.42));
      root.style.setProperty('--team-secondary-soft', hexToRgba(theme.secondary, 0.38));
      teamTitle.textContent = `${{team}} Roster`;
      teamFlag.textContent = '';
      teamFlag.style.backgroundImage = theme.flagCode
        ? `url("https://flagcdn.com/w80/${{theme.flagCode}}.png"), linear-gradient(90deg, ${{theme.primary}} 0 34%, ${{theme.secondary}} 34% 67%, ${{accent}} 67% 100%)`
        : '';
      teamFlag.setAttribute('aria-label', `${{team}} flag`);
    }}

    function readableText(hex) {{
      return luminance(hex) > 0.48 ? '#111827' : '#ffffff';
    }}

    function luminance(hex) {{
      const [red, green, blue] = rgbParts(hex).map(value => {{
        const channel = value / 255;
        return channel <= 0.03928
          ? channel / 12.92
          : Math.pow((channel + 0.055) / 1.055, 2.4);
      }});
      return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
    }}

    function shade(hex, amount) {{
      const parts = rgbParts(hex).map(value => {{
        const target = amount < 0 ? 0 : 255;
        return Math.round(value + (target - value) * Math.abs(amount));
      }});
      return `#${{parts.map(value => value.toString(16).padStart(2, '0')).join('')}}`;
    }}

    function rgbParts(hex) {{
      const value = hex.replace('#', '');
      return [
        parseInt(value.slice(0, 2), 16),
        parseInt(value.slice(2, 4), 16),
        parseInt(value.slice(4, 6), 16),
      ];
    }}

    function hexToRgba(hex, alpha) {{
      const [red, green, blue] = rgbParts(hex);
      return `rgba(${{red}}, ${{green}}, ${{blue}}, ${{alpha}})`;
    }}

    function escapeHtml(value) {{
      return String(value ?? '').replace(/[&<>"']/g, character => ({{
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
      }}[character]));
    }}

    function linkMarkup(label, url) {{
      const safeLabel = escapeHtml(label);
      if (!url) {{
        return safeLabel;
      }}
      return `<a class="wikilink" href="${{escapeHtml(url)}}" target="_blank" rel="noopener noreferrer">${{safeLabel}}</a>`;
    }}

    function playerMarkup(row) {{
      return linkMarkup(row.player, row.playerUrl);
    }}

    function fifproStarMarkup(row) {{
      return Number(row.fifproApps || 0) > 0
        ? `<span class="fifpro-star" title="FIFPRO World 11">${{escapeHtml('★')}}</span>`
        : '';
    }}

    function clubMarkup(row) {{
      if (!row.club) {{
        return '<span class="muted">-</span>';
      }}
      const logo = row.clubLogoUrl
        ? `<img class="club-logo" src="${{escapeHtml(row.clubLogoUrl)}}" alt="" loading="lazy">`
        : '';
      return `<span class="club">${{logo}}<span>${{linkMarkup(row.club, row.clubUrl)}}</span></span>`;
    }}

    teamSelect.addEventListener('change', event => renderTeam(event.target.value));
    renderTeam(teamSelect.value);
    fetchScoreboard();
  </script>
</body>
</html>
""",
        encoding="utf-8",
    )

    print(f"Wrote {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
