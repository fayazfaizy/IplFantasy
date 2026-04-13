import csv, json, sys, requests
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher
from pathlib import Path

BASE_DIR = Path(__file__).parent
DOCS_DIR = BASE_DIR.parent / "docs"
TEAMS_CSV = BASE_DIR / "teams.csv"
BEFORE_SCORES_FILE = BASE_DIR / "before_scores.json"
API_URL = "https://fantasy.iplt20.com/classic/api/feed/live/gamedayplayers"

MIXAPI_URL = "https://fantasy.iplt20.com/classic/api/live/mixapi"

API_PARAMS = {
    "lang": "en",
    "liveVersion": "1081",
    "announcedVersion": "04092026144844",
}

API_HEADERS = {
    "accept": "application/json",
    "content-type": "application/json;charset=utf-8",
    "entity": "d3tR0!t5m@sh",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}

API_COOKIES = {
    "my11c-uid": "3156017999",
    "my11c-authToken": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhdXRoIiwicHJvZHVjdF90eXBlIjoyLCJzZXNzaW9uSWQiOiJPRlJlYVVPUkJWaGIwVjVvZGRyOWxoSEd1MW93TXQzdVF4dGRzb0J1cWY1M2doc09pTktHa0lWanBZd0VZSHV1IiwidXNlcklkIjoxMzcxODQ4MDEsIndoYXRzYXBwQ2FsbCI6ZmFsc2UsImlhdCI6MTc3NTc0NjI3MCwiZXhwIjoxNzc1NzUzNDcwfQ.m6Ol-tyZ4wau_gNaro7-0G_HTbWuxRZYTuENRV1fI4U",
}

TEAM_COLORS = {
    "RCB": "#d4213d", "CSK": "#f9cd05", "MI": "#004ba0",
    "SRH": "#ff822a", "PBKS": "#dd1f2d", "RR": "#ea1a85",
}

PLAYER_PRICES = {
    "Virat Kohli": 305, "Travis Head": 160, "Aiden Markram": 140, "Arshdeep Singh": 100,
    "KL Rahul": 85, "Varun Chakaravarthy": 65, "Rajat Patidar": 40, "Rinku Singh": 20,
    "Ruturaj Gaikwad": 25, "Vipraj Nigam": 10, "Shashank Singh": 10, "Noor Ahmad": 10,
    "Harsh Dubey": 10, "Tushar Deshpande": 10, "Vijaykumar Vyshak": 10,
    "Shreyas Iyer": 270, "Ravindra Jadeja": 155, "Nicholas Pooran": 190, "Jos Buttler": 160,
    "Shimron Hetmyer": 55, "Harshal Patel": 20, "Ajinkya Rahane": 40, "Vaibhav Arora": 15,
    "Liam Livingstone": 15, "Rahul Tewatia": 15, "Jitesh Sharma": 15, "Marcus Stoinis": 15,
    "Romario Shepherd": 15, "Cameron Green": 10, "Kagiso Rabada": 10,
    "Abhishek Sharma": 200, "Yashasvi Jaiswal": 190, "Mitchell Marsh": 110, "Rishabh Pant": 90,
    "Yuzvendra Chahal": 70, "Marco Jansen": 70, "Nitish Kumar Reddy": 35, "Ryan Rickelton": 40,
    "Vaibhav Sooryavanshi": 50, "Tim David": 40, "Tristan Stubbs": 20, "Shardul Thakur": 20,
    "Riyan Parag": 20, "Mitchell Santner": 35, "Eshan Malinga": 10,
    "Suryakumar Yadav": 170, "Sunil Narine": 150, "Rohit Sharma": 200, "Tilak Varma": 120,
    "Jofra Archer": 60, "Priyansh Arya": 60, "Nehal Wadhera": 30, "Mohammed Siraj": 20,
    "Deepak Chahar": 20, "Prabhsimran Singh": 40, "Ayush Mhatre": 45, "Bhuvneshwar Kumar": 30,
    "Aniket Verma": 15, "David Miller": 20, "Sherfane Rutherford": 10,
    "Jasprit Bumrah": 170, "Heinrich Klaasen": 205, "Shivam Dube": 170, "Sai Sudharsan": 190,
    "Axar Patel": 90, "Naman Dhir": 25, "Angkrish Raghuvanshi": 50, "Krunal Pandya": 30,
    "Ayush Badoni": 10, "Mohammad Shami": 10, "Washington Sundar": 10, "Jamie Overton": 10,
    "Lungi Ngidi": 10, "Glenn Phillips": 10, "Jacob Duffy": 10,
    "Ishan Kishan": 230, "Hardik Pandya": 190, "Shubman Gill": 110, "Phil Salt": 85,
    "Rashid Khan": 55, "Kuldeep Yadav": 30, "Sanju Samson": 70, "Khaleel Ahmed": 20,
    "Devdutt Padikkal": 35, "Dhruv Jurel": 40, "Prasidh Krishna": 25, "Sameer Rizvi": 25,
    "Anshul Kamboj": 10, "Ravi Bishnoi": 15, "Cooper Connolly": 20,
}


def load_teams():
    teams = []
    with open(TEAMS_CSV) as f:
        for row in csv.DictReader(f):
            players = [row[f"Player{i}"].strip() for i in range(1, 17) if row.get(f"Player{i}", "").strip()]
            teams.append({"team": row["Team"], "owners": [row["Owner1"], row["Owner2"]], "players": players})
    return teams


def fetch_api_players():
    mix = requests.get(MIXAPI_URL, params={"lang": "en"}, headers=API_HEADERS, cookies=API_COOKIES)
    mix.raise_for_status()
    gameday_id = mix.json()["Data"]["Value"].get("GamedayId")
    if not gameday_id:
        print("No active GamedayId, skipping update.")
        return None
    print(f"Using GamedayId: {gameday_id}")
    params = {**API_PARAMS, "tourgamedayId": gameday_id, "teamgamedayId": gameday_id}
    resp = requests.get(API_URL, params=params, headers=API_HEADERS, cookies=API_COOKIES)
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
        for pname in team["players"]:
            matched = fuzzy_match(pname, api_players)
            if matched:
                current = matched["OverallPoints"]
                today = matched["GamedayPoints"]
                baseline = before.get(matched["Name"], current)
                delta = current - baseline
                player_details.append({"name": matched["Name"], "ipl_team": matched["TeamShortName"], "before": baseline, "current": current, "today": today, "points": delta})
            else:
                player_details.append({"name": pname + " ❌", "ipl_team": "", "before": 0, "current": 0, "today": 0, "points": 0})
        players_sorted = sorted(player_details, key=lambda x: x["points"], reverse=True)
        total = sum(p["points"] for p in players_sorted[:11])
        today_total = sum(p["today"] for p in players_sorted[:11])
        team_results.append({
            "team": team["team"], "owners": " & ".join(team["owners"]),
            "total": total, "today_total": today_total, "players": players_sorted,
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
          <td class="num today-pts">{t['today_total']:+.0f}</td>
          <td class="pts">{t['total']:.0f}</td>
        </tr>"""

    team_cards = ""
    for t in team_results:
        color = TEAM_COLORS.get(t["team"], "#666")
        rows = ""
        for i, p in enumerate(t["players"]):
            pts_class = "pos" if p["points"] > 0 else "neg" if p["points"] < 0 else ""
            bench = " bench" if i >= 11 else ""
            price = PLAYER_PRICES.get(p['name'], 0)
            pct = round(p['points'] / t['total'] * 100, 1) if t['total'] else 0
            pct_str = f"{pct:.1f}" if pct != int(pct) else f"{int(pct)}"
            rows += f"""
            <tr class="{bench.strip()}">
              <td>{p['name']} <span class="ipl-team">{p['ipl_team']}</span></td>
              <td class="num price">{price}L</td>
              <td class="num col-bc">{p['before']:.0f}</td>
              <td class="num col-bc">{p['current']:.0f}</td>
              <td class="num today-pts">{p['today']:+.0f}</td>
              <td class="num {pts_class}">{p['points']:+.0f}</td>
              <td class="num pct">{pct_str}%</td>
            </tr>"""
        team_cards += f"""
    <div class="card">
      <div class="card-header" style="background:{color}">{t['team']} — {t['owners']} <span class="card-pts">{t['total']:.0f} pts</span></div>
      <div class="table-wrap">
      <table class="player-table">
        <thead><tr><th onclick="sortTable(this)">Player</th><th onclick="sortTable(this)">Price</th><th onclick="sortTable(this)" class="col-bc">Before</th><th onclick="sortTable(this)" class="col-bc">Current</th><th onclick="sortTable(this)">Today</th><th onclick="sortTable(this)">Points</th><th onclick="sortTable(this)">%</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      </div>
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
  .bench {{ opacity: 0.4; }}
  .today-pts {{ font-size: 1em; font-weight: 600; color: #f9cd05; text-align: right; }}
  .price {{ color: #4cff9f; font-size: 0.85em; }}
  .pct {{ color: #aaa; font-size: 0.85em; }}
  .col-toggle {{ display: inline-block; margin: 0 0 12px; padding: 5px 14px; background: #1a1f3d; color: #aaa; border: 1px solid #2a2f55; border-radius: 6px; font-size: 0.8em; cursor: pointer; user-select: none; }}
  .col-toggle.active {{ color: #4cff9f; border-color: #4cff9f; }}
  .hide-bc .col-bc {{ display: none; }}
  .ipl-team {{ font-size: 0.7em; background: #2a2f55; padding: 1px 6px; border-radius: 3px; margin-left: 6px; color: #aaa; vertical-align: middle; }}
  .table-wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
  .leaderboard th, .player-table th {{ cursor: pointer; user-select: none; }}
  .leaderboard th:hover, .player-table th:hover {{ color: #fff; }}
  th.sort-asc::after {{ content: ' ▲'; font-size: 0.75em; }}
  th.sort-desc::after {{ content: ' ▼'; font-size: 0.75em; }}
  @media (max-width: 600px) {{
    .container {{ padding: 10px; }}
    h1 {{ font-size: 1.4em; }}
    .leaderboard th, .leaderboard td {{ padding: 8px 6px; font-size: 0.85em; }}
    .rank {{ font-size: 1.1em; width: 36px; }}
    .pts {{ font-size: 1.1em; }}
    .team-badge {{ padding: 3px 8px; font-size: 0.75em; }}
    .card-header {{ padding: 10px 12px; font-size: 0.95em; }}
    .player-table th, .player-table td {{ padding: 6px 8px; font-size: 0.8em; }}
  }}
</style>
</head>
<body>
<div class="container hide-bc">
  <h1>🏏 IPL Fantasy League</h1>
  <p class="subtitle">Updated: {now}</p>
  <div class="table-wrap">
  <table class="leaderboard">
    <thead><tr><th onclick="sortTable(this)"></th><th onclick="sortTable(this)">Team</th><th onclick="sortTable(this)">Owners</th><th onclick="sortTable(this)" style="text-align:right">Today</th><th onclick="sortTable(this)" style="text-align:right">Total</th></tr></thead>
    <tbody>{leaderboard_rows}</tbody>
  </table>
  </div>
  <span class="col-toggle" onclick="toggleBC(this)">Show Before / Current</span>
  {team_cards}
</div>
<script>
function toggleBC(btn) {{
  document.querySelector('.container').classList.toggle('hide-bc');
  btn.classList.toggle('active');
}}
function sortTable(th) {{
  const table = th.closest('table');
  const tbody = table.querySelector('tbody');
  const idx = Array.from(th.parentElement.children).indexOf(th);
  const asc = !th.classList.contains('sort-asc');
  table.querySelectorAll('th').forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
  th.classList.add(asc ? 'sort-asc' : 'sort-desc');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  rows.sort((a, b) => {{
    const av = a.children[idx]?.textContent.trim().replace(/[^\d.-]/g, '') || '';
    const bv = b.children[idx]?.textContent.trim().replace(/[^\d.-]/g, '') || '';
    const an = parseFloat(av), bn = parseFloat(bv);
    if (!isNaN(an) && !isNaN(bn)) return asc ? an - bn : bn - an;
    return asc ? av.localeCompare(bv) : bv.localeCompare(av);
  }});
  rows.forEach(r => tbody.appendChild(r));
}}
</script>
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
    if not api_players:
        return
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
