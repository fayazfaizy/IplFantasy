import csv, json, sys, requests
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher
from pathlib import Path

BASE_DIR = Path(__file__).parent
DOCS_DIR = BASE_DIR.parent / "docs"
TEAMS_CSV = BASE_DIR / "teams.csv"
BEFORE_SCORES_FILE = BASE_DIR / "before_scores.json"
API_URL = "https://fantasy.iplt20.com/classic/api/feed/live/gamedayplayers"

API_PARAMS = {
    "lang": "en",
    "tourgamedayId": "14",
    "teamgamedayId": "14",
    "liveVersion": "1018",
    "announcedVersion": "04082026154210",
}

API_HEADERS = {
    "accept": "application/json",
    "content-type": "application/json;charset=utf-8",
    "entity": "d3tR0!t5m@sh",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}

API_COOKIES = {
    "my11c-uid": "3156017999",
    "my11c-authToken": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhdXRoIiwicHJvZHVjdF90eXBlIjoyLCJzZXNzaW9uSWQiOiIyTFE0VXJZSzR3dnVudVliMDYvTXVzUm9CK3BwdEd1VHhpVUYxYXVIZ0JKQ3pmVVpKUk1EQnE0akt6MFJVdGNOIiwidXNlcklkIjoxMzcxODQ4MDEsIndoYXRzYXBwQ2FsbCI6ZmFsc2UsImlhdCI6MTc3NTY2Mjk0NiwiZXhwIjoxNzc1NjcwMTQ2fQ.oPm8JY4zxI-kwFbrFxyNW4Mr0WriqcYpDqc1Spi6Fq4",
}

TEAM_COLORS = {
    "RCB": "#d4213d", "CSK": "#f9cd05", "MI": "#004ba0",
    "SRH": "#ff822a", "PBKS": "#dd1f2d", "RR": "#ea1a85",
}


def load_teams():
    teams = []
    with open(TEAMS_CSV) as f:
        for row in csv.DictReader(f):
            players = [row[f"Player{i}"].strip() for i in range(1, 17) if row.get(f"Player{i}", "").strip()]
            teams.append({"team": row["Team"], "owners": [row["Owner1"], row["Owner2"]], "players": players})
    return teams


def fetch_api_players():
    resp = requests.get(API_URL, params=API_PARAMS, headers=API_HEADERS, cookies=API_COOKIES)
    resp.raise_for_status()
    return resp.json()["Data"]["Value"]["Players"]


def fuzzy_match(name, candidates, threshold=0.5):
    name_lower = name.lower().strip()
    best, best_score = None, 0
    for c in candidates:
        full = c["Name"].lower()
        if name_lower in full or full in name_lower:
            return c
        for part in full.split():
            if name_lower == part:
                return c
        score = SequenceMatcher(None, name_lower, full).ratio()
        if score > best_score:
            best_score, best = score, c
    return best if best_score >= threshold else None


def load_before_scores():
    if BEFORE_SCORES_FILE.exists():
        with open(BEFORE_SCORES_FILE) as f:
            return json.load(f)
    return {}


def save_before_scores(scores):
    with open(BEFORE_SCORES_FILE, "w") as f:
        json.dump(scores, f, indent=2)


def snapshot_before(api_players):
    if BEFORE_SCORES_FILE.exists():
        existing = load_before_scores()
        taken = existing.get("_snapshot_date", "unknown")
        ans = input(f"⚠️  Baseline already exists (taken: {taken}). Overwrite? [y/N]: ")
        if ans.lower() != "y":
            print("Aborted.")
            return
    scores = {p["Name"]: p["OverallPoints"] for p in api_players}
    scores["_snapshot_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_before_scores(scores)
    print(f"✅ Saved before scores for {len(scores) - 1} players to {BEFORE_SCORES_FILE}")


def build_results(teams, api_players):
    before = load_before_scores()
    if not before:
        return None
    team_results = []
    for team in teams:
        player_details = []
        total = 0
        for pname in team["players"]:
            matched = fuzzy_match(pname, api_players)
            if matched:
                current = matched["OverallPoints"]
                baseline = before.get(matched["Name"], current)
                delta = current - baseline
                player_details.append({"name": matched["Name"], "before": baseline, "current": current, "points": delta})
                total += delta
            else:
                player_details.append({"name": pname + " ❌", "before": 0, "current": 0, "points": 0})
        team_results.append({
            "team": team["team"], "owners": " & ".join(team["owners"]),
            "total": total, "players": sorted(player_details, key=lambda x: x["points"], reverse=True),
        })
    team_results.sort(key=lambda x: x["total"], reverse=True)
    return team_results


def print_leaderboard(team_results):
    print("\n" + "=" * 80)
    print(f"{'Rank':<6}{'Team':<8}{'Owners':<22}{'Total Points':>12}")
    print("=" * 80)
    for i, t in enumerate(team_results, 1):
        print(f"{i:<6}{t['team']:<8}{t['owners']:<22}{t['total']:>12.0f}")
    print("=" * 80)
    for t in team_results:
        print(f"\n{'─' * 70}")
        print(f"  {t['team']} ({t['owners']}) — Total: {t['total']:.0f} pts")
        print(f"  {'Player':<25}{'Before':>10}{'Current':>10}{'Points':>10}")
        print(f"  {'─' * 55}")
        for p in t["players"]:
            print(f"  {p['name']:<25}{p['before']:>10.0f}{p['current']:>10.0f}{p['points']:>10.0f}")


def generate_html(team_results):
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist).strftime("%d %b %Y, %I:%M %p IST")

    leaderboard_rows = ""
    for i, t in enumerate(team_results, 1):
        color = TEAM_COLORS.get(t["team"], "#666")
        medal = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"#{i}"
        leaderboard_rows += f"""
        <tr>
          <td class="rank">{medal}</td>
          <td><span class="team-badge" style="background:{color}">{t['team']}</span></td>
          <td>{t['owners']}</td>
          <td class="pts">{t['total']:.0f}</td>
        </tr>"""

    team_cards = ""
    for t in team_results:
        color = TEAM_COLORS.get(t["team"], "#666")
        rows = ""
        for p in t["players"]:
            pts_class = "pos" if p["points"] > 0 else "neg" if p["points"] < 0 else ""
            rows += f"""
            <tr>
              <td>{p['name']}</td>
              <td class="num">{p['before']:.0f}</td>
              <td class="num">{p['current']:.0f}</td>
              <td class="num {pts_class}">{p['points']:+.0f}</td>
            </tr>"""
        team_cards += f"""
    <div class="card">
      <div class="card-header" style="background:{color}">{t['team']} — {t['owners']} <span class="card-pts">{t['total']:.0f} pts</span></div>
      <table class="player-table">
        <thead><tr><th>Player</th><th>Before</th><th>Current</th><th>Points</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IPL Fantasy League</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0a0e27; color: #e0e0e0; min-height: 100vh; }}
  .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
  h1 {{ text-align: center; font-size: 2em; margin: 20px 0 5px; background: linear-gradient(135deg, #f9cd05, #ea1a85, #004ba0); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
  .subtitle {{ text-align: center; color: #888; margin-bottom: 30px; font-size: 0.9em; }}
  .leaderboard {{ width: 100%; border-collapse: collapse; margin-bottom: 40px; }}
  .leaderboard th {{ background: #1a1f3d; padding: 12px; text-align: left; font-size: 0.85em; text-transform: uppercase; color: #aaa; }}
  .leaderboard td {{ padding: 14px 12px; border-bottom: 1px solid #1a1f3d; }}
  .leaderboard tr:hover {{ background: #12163a; }}
  .rank {{ font-size: 1.3em; width: 50px; text-align: center; }}
  .team-badge {{ padding: 4px 12px; border-radius: 4px; color: #fff; font-weight: 700; font-size: 0.85em; }}
  .pts {{ font-size: 1.4em; font-weight: 700; color: #4cff9f; text-align: right; }}
  .card {{ background: #111535; border-radius: 10px; overflow: hidden; margin-bottom: 20px; }}
  .card-header {{ padding: 14px 20px; color: #fff; font-weight: 700; font-size: 1.1em; display: flex; justify-content: space-between; }}
  .card-pts {{ background: rgba(255,255,255,0.2); padding: 2px 10px; border-radius: 12px; font-size: 0.9em; }}
  .player-table {{ width: 100%; border-collapse: collapse; }}
  .player-table th {{ background: #0d1029; padding: 8px 16px; text-align: left; font-size: 0.8em; text-transform: uppercase; color: #777; }}
  .player-table td {{ padding: 8px 16px; border-bottom: 1px solid #1a1f3d; font-size: 0.9em; }}
  .player-table tr:hover {{ background: #161b40; }}
  .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .pos {{ color: #4cff9f; font-weight: 700; }}
  .neg {{ color: #ff4c6a; font-weight: 700; }}
</style>
</head>
<body>
<div class="container">
  <h1>🏏 IPL Fantasy League</h1>
  <p class="subtitle">Updated: {now}</p>
  <table class="leaderboard">
    <thead><tr><th></th><th>Team</th><th>Owners</th><th style="text-align:right">Points</th></tr></thead>
    <tbody>{leaderboard_rows}</tbody>
  </table>
  {team_cards}
</div>
</body>
</html>"""

    out = DOCS_DIR / "index.html"
    out.write_text(html)
    print(f"✅ Generated {out}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python fantasy.py [snapshot|leaderboard|html]")
        print("  snapshot    — Save current scores as baseline")
        print("  leaderboard — Print leaderboard to terminal")
        print("  html        — Generate docs/index.html for GitHub Pages")
        return

    cmd = sys.argv[1]
    teams = load_teams()

    if cmd == "snapshot":
        print("Fetching player data...")
        api_players = fetch_api_players()
        snapshot_before(api_players)
        return

    print("Fetching player data...")
    api_players = fetch_api_players()
    print(f"Fetched {len(api_players)} players.")
    results = build_results(teams, api_players)
    if not results:
        print("⚠️  No before_scores.json found. Run 'snapshot' first.")
        return

    if cmd == "leaderboard":
        print_leaderboard(results)
    elif cmd == "html":
        print_leaderboard(results)
        generate_html(results)
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
