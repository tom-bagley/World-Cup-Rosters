$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

python .\fetch_world_cup_rosters.py
python .\build_roster_viewer.py
python .\update_goals_from_kalshi.py
python .\price_world_cup_teams.py
python .\sync_standings_expected_points.py
